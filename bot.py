"""
Telegram-бот "Marina Twin" — штатный юрист по праву РФ, ВЭД и крипто
в СНГ/Таможенном союзе/ЕАЭС. Интерфейс поверх Claude API с кэшированной базой
знаний и точечной подгрузкой странового модуля по ходу разговора.

Запуск: python bot.py
Нужны переменные окружения: TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY (см. .env.example).
"""

import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

import claude_client
import clickup_client
import config
import kb
import storage
import task_extractor

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("marina_twin_bot")

TELEGRAM_MESSAGE_LIMIT = 4096


def _is_allowed(user_id: int) -> bool:
    if config.ALLOWED_USER_IDS is None:
        return True
    return user_id in config.ALLOWED_USER_IDS


def _split_for_telegram(text: str) -> list[str]:
    """Режет длинный ответ на куски под лимит Telegram, стараясь резать по абзацам."""
    if len(text) <= TELEGRAM_MESSAGE_LIMIT:
        return [text]

    chunks = []
    remaining = text
    while len(remaining) > TELEGRAM_MESSAGE_LIMIT:
        cut = remaining.rfind("\n\n", 0, TELEGRAM_MESSAGE_LIMIT)
        if cut == -1:
            cut = remaining.rfind(" ", 0, TELEGRAM_MESSAGE_LIMIT)
        if cut == -1:
            cut = TELEGRAM_MESSAGE_LIMIT
        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks


def _update_active_countries(active: list[str], mentioned: set[str], russia_only: bool) -> list[str]:
    if russia_only:
        return []
    if not mentioned:
        return active
    # Новые упоминания — в начало (приоритет), без дублей, обрезаем по лимиту.
    updated = list(mentioned) + [c for c in active if c not in mentioned]
    return updated[: kb.MAX_ACTIVE_COUNTRIES]


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    storage.reset_chat(update.effective_chat.id)
    await update.message.reply_text(
        "Привет! Я на связи 🙂 Пиши, с чем помочь — я тут же подключусь."
    )


async def handle_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    storage.reset_chat(update.effective_chat.id)
    await update.message.reply_text("Хорошо, начинаем разговор заново.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    text = update.message.text or ""

    if not _is_allowed(user.id):
        logger.warning("Отклонён неразрешённый пользователь %s (%s)", user.id, user.username)
        await update.message.reply_text(
            "Извини, этот бот только для сотрудников. Если это ошибка — напиши Марине."
        )
        return

    state = storage.get_chat(chat_id)
    history: list = state["history"]
    active_countries: list = state["active_countries"]
    greeted: bool = state["greeted"]

    mentioned = kb.detect_countries(text)
    russia_only = kb.mentions_russia_only(text)
    active_countries = _update_active_countries(active_countries, mentioned, russia_only)
    if mentioned:
        logger.info("Чат %s: обнаружены страны %s, активный набор: %s", chat_id, mentioned, active_countries)

    first_name = user.first_name or ""
    prefixed_text = text
    if not greeted:
        prefixed_text = f"[Это первое сообщение в разговоре. Имя собеседника: {first_name or 'неизвестно'}.]\n\n{text}"

    history.append({"role": "user", "content": prefixed_text})

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        reply = claude_client.ask_marina_twin(history, active_countries)
    except Exception:
        logger.exception("Ошибка при обращении к Claude API")
        await update.message.reply_text(
            "Ой, что-то у меня зависло при обращении к базе, давай попробуем ещё раз через минутку 🙏"
        )
        return

    history.append({"role": "assistant", "content": reply})
    storage.save_chat(chat_id, history, active_countries, greeted=True)

    for chunk in _split_for_telegram(reply):
        await update.message.reply_text(chunk)


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """В групповых чатах Marina Twin молча слушает и копит переписку — не отвечает,
    не участвует в разговоре. Задачи из накопленного вытаскиваются по команде /tasks
    или автоматически по расписанию (см. periodic_flush_job)."""
    chat = update.effective_chat
    user = update.effective_user
    text = update.message.text or ""
    if not text.strip():
        return
    user_name = (user.first_name or user.username or "кто-то") if user else "кто-то"
    storage.add_group_message(chat.id, chat.title or str(chat.id), user_name, text)


async def _flush_chat_to_clickup(chat_id: int, chat_title: str) -> int:
    """Извлекает задачи из накопленных сообщений одного чата и пушит их в ClickUp.
    Возвращает число созданных задач. Буфер помечается прочитанным в любом случае —
    иначе при постоянной ошибке ClickUp одни и те же старые сообщения будут
    пересчитываться на каждой выгрузке."""
    rows = storage.get_unflushed(chat_id)
    if not rows:
        return 0

    try:
        tasks = task_extractor.extract_tasks(chat_title, rows)
    except Exception:
        logger.exception("Ошибка извлечения задач для чата %s (%s)", chat_id, chat_title)
        storage.mark_flushed(chat_id)
        return 0

    created = 0
    for t in tasks:
        title = (t.get("title") or "").strip()
        if not title:
            continue
        try:
            result = clickup_client.create_task(
                name=title,
                description=t.get("description", ""),
                priority=t.get("priority"),
            )
            storage.log_pushed_task(chat_id, chat_title, str(result.get("id", "")), title)
            created += 1
        except Exception:
            logger.exception("Не удалось создать задачу в ClickUp: %s", title)

    storage.mark_flushed(chat_id)
    return created


async def handle_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text(
            "Эта команда собирает задачи из группового чата — вызови её внутри нужной группы."
        )
        return
    if not config.CLICKUP_ENABLED:
        await update.message.reply_text(
            "ClickUp пока не подключен (нет CLICKUP_API_TOKEN/CLICKUP_LIST_ID в настройках) — задачи копятся, но выгружать пока некуда."
        )
        return

    await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)
    created = await _flush_chat_to_clickup(chat.id, chat.title or str(chat.id))
    if created:
        await update.message.reply_text(f"Готово, добавила {created} задач(и) в ClickUp 👍")
    else:
        await update.message.reply_text("Новых задач в переписке с прошлого раза не нашла.")


async def periodic_flush_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Фоновая выгрузка задач из всех групп сразу — по расписанию
    (CLICKUP_FLUSH_INTERVAL_MINUTES), без ручной команды."""
    if not config.CLICKUP_ENABLED:
        return
    for chat_id, chat_title in storage.get_chats_with_pending():
        created = await _flush_chat_to_clickup(chat_id, chat_title)
        if created:
            logger.info("Авто-выгрузка: чат «%s» (%s) → %d задач в ClickUp", chat_title, chat_id, created)


def build_application() -> Application:
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("reset", handle_reset))
    app.add_handler(CommandHandler("tasks", handle_tasks_command))
    # Личка — обычный разговор с персоной Marina Twin.
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_message))
    # Группы — тихий сбор переписки, без ответов.
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS, handle_group_message))

    if config.CLICKUP_ENABLED:
        interval = config.CLICKUP_FLUSH_INTERVAL_MINUTES * 60
        app.job_queue.run_repeating(periodic_flush_job, interval=interval, first=interval)
        logger.info("ClickUp-интеграция включена, автовыгрузка каждые %d мин.", config.CLICKUP_FLUSH_INTERVAL_MINUTES)
    else:
        logger.info("ClickUp-интеграция выключена (нет CLICKUP_API_TOKEN/CLICKUP_LIST_ID) — сбор задач копится, но никуда не уходит.")

    return app


def main() -> None:
    # claude_client уже при импорте выше загрузил базу знаний (см. kb.load_core внутри него)
    logger.info("База загружена, запускаю бота (модель: %s)", config.MODEL_NAME)
    app = build_application()
    app.run_polling()


if __name__ == "__main__":
    main()
