"""
Telegram-бот "Marina Twin" — штатный юрист по праву РФ, ВЭД и крипто
в СНГ/Таможенном союзе/ЕАЭС. Интерфейс поверх Claude API с кэшированной базой
знаний и точечной подгрузкой странового модуля по ходу разговора.

Запуск: python bot.py
Нужны переменные окружения: TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY (см. .env.example).
"""

import logging
import random
import re

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

import claude_client
import clickup_client
import config
import escalation
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


# --- Закрепление группового чата за проектом по фразе в сообщении ---
# ("эта группа про задачи Altyn", "это группа для задач Atlas", "это группа Bestswift/BS")

def _detect_project_binding(text: str) -> str | None:
    """Ищет в сообщении совместное упоминание слова "групп-" и ключевого слова одного
    из проектов (см. config.CLICKUP_PROJECTS[...]["keywords"]) — этого достаточно для
    явных фраз вида "эта группа про задачи <проект>", без отдельной команды."""
    lowered = text.lower()
    if "групп" not in lowered:
        return None
    for key, project in config.CLICKUP_PROJECTS.items():
        for kw in project["keywords"]:
            if re.search(r"\b" + re.escape(kw) + r"\b", lowered):
                return key
    return None


# --- Обращение к "Марине" в группе (упоминание, reply, имя) ---

_MARINA_NAME_RE = re.compile(r"\bмарин(а|ы|е|у|ой|ою)\b|\bmarina\b", re.IGNORECASE)

_ACK_PHRASES = [
    "Секунду, уточню и вернусь 🙂",
    "Дай мне минутку — уточню и отвечу.",
    "Сейчас, только уточню детали — и сразу вернусь с ответом.",
]


def _is_addressed_to_marina(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    bot_username = context.bot.username
    if bot_username and f"@{bot_username.lower()}" in text.lower():
        return True
    reply_to = update.message.reply_to_message
    if reply_to and reply_to.from_user and reply_to.from_user.id == context.bot.id:
        return True
    return bool(_MARINA_NAME_RE.search(text))


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    storage.reset_chat(update.effective_chat.id)
    await update.message.reply_text(
        "Привет! Я на связи 🙂 Пиши, с чем помочь — я тут же подключусь."
    )


async def handle_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    storage.reset_chat(update.effective_chat.id)
    await update.message.reply_text("Хорошо, начинаем разговор заново.")


async def _resolve_escalation(
    update: Update, context: ContextTypes.DEFAULT_TYPE, pending: tuple, answer_text: str
) -> None:
    """Владелица ответила в личке на вопрос, ранее пересланный из группы (см.
    handle_group_message). Перефразируем её ответ от её лица и публикуем в исходной
    группе — коллеги видят обычный ответ "Марины", не зная про пересылку в личку."""
    esc_id, group_chat_id, group_title, asker_name, question = pending

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    try:
        final_text = escalation.rephrase_answer(group_title, asker_name, question, answer_text)
    except Exception:
        logger.exception("Не удалось перефразировать ответ для эскалации #%s — отправляю как есть", esc_id)
        final_text = answer_text

    try:
        await context.bot.send_message(chat_id=group_chat_id, text=final_text)
    except Exception:
        logger.exception("Не удалось отправить ответ в группу %s (эскалация #%s)", group_chat_id, esc_id)
        storage.resolve_pending_escalation(esc_id)
        await update.message.reply_text(
            f"Поняла ответ, но не смогла отправить его в «{group_title}» (возможно, меня там больше нет) — "
            f"перешли, пожалуйста, вручную: {final_text}"
        )
        return

    storage.resolve_pending_escalation(esc_id)
    await update.message.reply_text(f"Готово, ответила в «{group_title}» 👍")


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

    # Если пишет владелица и её ждёт неотвеченный вопрос из группы — это её ответ на
    # НЕГО, а не обычная реплика персоне. Забираем самый старый неотвеченный вопрос.
    if config.OWNER_USER_ID is not None and user.id == config.OWNER_USER_ID:
        pending = storage.get_oldest_pending_escalation()
        if pending:
            await _resolve_escalation(update, context, pending, text)
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
    """В групповых чатах Marina Twin по умолчанию молча слушает и копит переписку —
    не отвечает, не участвует в разговоре. Два исключения:
    (1) сообщение закрепляет чат за проектом ("эта группа про задачи Altyn") —
        отвечает подтверждением;
    (2) к ней явно обращаются (@упоминание, reply на её сообщение, имя "Марина") —
        отвечает "сейчас вернусь" и пересылает вопрос владелице в личку (см. handle_message).
    Иначе сообщение просто уходит в буфер — задачи из него достаются командой
    /tasksatlas /tasksaltyn /tasksbs, либо автоматически по расписанию
    (см. periodic_flush_job) для уже привязанных к проекту чатов, либо (для чатов без
    привязки) классифицируются по проекту индивидуально при автовыгрузке."""
    chat = update.effective_chat
    user = update.effective_user
    text = update.message.text or ""
    if not text.strip():
        return

    bound_project = _detect_project_binding(text)
    if bound_project:
        storage.set_chat_project(chat.id, bound_project)
        label = config.CLICKUP_PROJECTS[bound_project]["label"]
        await update.message.reply_text(f"Поняла, буду собирать сюда задачи по проекту «{label}» 👍")
        return

    if _is_addressed_to_marina(update, context, text):
        if config.OWNER_USER_ID is not None:
            await update.message.reply_text(random.choice(_ACK_PHRASES))
            asker_name = (user.first_name or user.username or "коллега") if user else "коллега"
            storage.add_pending_escalation(chat.id, chat.title or str(chat.id), asker_name, text)
            try:
                await context.bot.send_message(
                    chat_id=config.OWNER_USER_ID,
                    text=(
                        f"❓ Вопрос из группы «{chat.title or chat.id}» от {asker_name}:\n\n{text}\n\n"
                        f"Ответь мне сюда обычным сообщением — перескажу это в чат."
                    ),
                )
            except Exception:
                logger.exception("Не удалось отправить эскалацию владелице (user_id=%s)", config.OWNER_USER_ID)
            return
        logger.warning(
            "Обращение к Марине в чате %s, но MARINATWIN_OWNER_USER_ID не настроен — "
            "эскалация выключена, сообщение уйдёт в обычный сбор задач.",
            chat.id,
        )

    user_name = (user.first_name or user.username or "кто-то") if user else "кто-то"
    storage.add_group_message(chat.id, chat.title or str(chat.id), user_name, text)


def _push_tasks(chat_id: int, chat_title: str, tasks: list[dict], list_id_for: callable) -> int:
    """Общая часть: создаёт в ClickUp каждую задачу из tasks, для которой list_id_for(t)
    вернул непустой список. Возвращает число реально созданных задач."""
    created = 0
    for t in tasks:
        title = (t.get("title") or "").strip()
        if not title:
            continue
        list_id = list_id_for(t)
        if not list_id:
            continue
        try:
            result = clickup_client.create_task(
                list_id,
                name=title,
                description=t.get("description", ""),
                priority=t.get("priority"),
            )
            storage.log_pushed_task(chat_id, chat_title, str(result.get("id", "")), title)
            created += 1
        except Exception:
            logger.exception("Не удалось создать задачу в ClickUp: %s", title)
    return created


async def _flush_chat_to_clickup(chat_id: int, chat_title: str, project_key: str | None) -> int:
    """Извлекает задачи из накопленных сообщений одного чата и пушит их в ClickUp.
    Возвращает число созданных задач. Буфер помечается прочитанным только после
    успешного извлечения и отправки задач — если извлечение упало (ошибка Claude API,
    таймаут, рейт-лимит), буфер остаётся непрочитанным и будет повторно обработан
    на следующей выгрузке.

    project_key задан → чат закреплён за одним проектом, все задачи туда, без
    классификации. project_key is None → "смешанный" чат без привязки: каждая задача
    классифицируется отдельно (Atlas/Алтын/BestSwift/Разобрать)."""
    rows = storage.get_unflushed(chat_id)
    if not rows:
        return 0

    if project_key:
        list_id = config.CLICKUP_LIST_IDS.get(project_key)
        if not list_id:
            # Проект закреплён, но список для него ещё не настроен — не теряем буфер,
            # просто ждём (не помечаем flushed, не тратим вызов Claude впустую).
            return 0
        try:
            tasks = task_extractor.extract_tasks(chat_title, rows)
        except Exception:
            logger.exception("Ошибка извлечения задач для чата %s (%s)", chat_id, chat_title)
            return 0
        created = _push_tasks(chat_id, chat_title, tasks, lambda _t: list_id)
    else:
        try:
            tasks = task_extractor.extract_tasks_classified(chat_title, rows)
        except Exception:
            logger.exception("Ошибка извлечения/классификации задач для чата %s (%s)", chat_id, chat_title)
            return 0

        def _list_for(t: dict) -> str | None:
            key = t.get("project") if t.get("project") in config.CLICKUP_LIST_IDS else "unsorted"
            return config.CLICKUP_LIST_IDS.get(key)

        created = _push_tasks(chat_id, chat_title, tasks, _list_for)

    storage.mark_flushed(chat_id)
    return created


def _make_tasks_command_handler(project_key: str):
    """Команды /tasksatlas /tasksaltyn /tasksbs — каждая для своего проекта.
    Вызов команды в чате: (1) немедленно выгружает накопленные задачи чата в список
    этого проекта, (2) закрепляет проект за чатом, чтобы дальше периодическая
    автовыгрузка (см. periodic_flush_job) сама знала, куда слать задачи из этого чата,
    без повторного вызова команды каждый раз."""
    label = config.CLICKUP_PROJECTS[project_key]["label"]

    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        if chat.type not in ("group", "supergroup"):
            await update.message.reply_text(
                "Эта команда собирает задачи из группового чата — вызови её внутри нужной группы."
            )
            return
        list_id = config.CLICKUP_LIST_IDS.get(project_key)
        if not config.CLICKUP_API_TOKEN or not list_id:
            await update.message.reply_text(
                f"Список ClickUp для проекта «{label}» пока не настроен — задачи копятся, но выгружать пока некуда."
            )
            return

        storage.set_chat_project(chat.id, project_key)
        await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)
        created = await _flush_chat_to_clickup(chat.id, chat.title or str(chat.id), project_key)
        if created:
            await update.message.reply_text(f"Готово, добавила {created} задач(и) в ClickUp ({label}) 👍")
        else:
            await update.message.reply_text(f"Новых задач в переписке с прошлого раза не нашла (проект «{label}»).")

    return handler


async def periodic_flush_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Фоновая выгрузка задач по расписанию (CLICKUP_FLUSH_INTERVAL_MINUTES), без
    ручной команды — для ВСЕХ чатов с непрочитанными сообщениями. Для чатов,
    закреплённых за проектом, задачи идут в его список; для "смешанных" чатов без
    привязки — классифицируются по отдельности (см. _flush_chat_to_clickup)."""
    if not config.CLICKUP_ENABLED:
        return
    for chat_id, chat_title in storage.get_chats_with_pending():
        project_key = storage.get_chat_project(chat_id)
        created = await _flush_chat_to_clickup(chat_id, chat_title, project_key)
        if created:
            logger.info(
                "Авто-выгрузка: чат «%s» (%s), проект %s → %d задач в ClickUp",
                chat_title, chat_id, project_key or "не закреплён (классификация)", created,
            )


def build_application() -> Application:
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("reset", handle_reset))
    # По команде на проект: /tasksatlas /tasksaltyn /tasksbs ("unsorted"/Разобрать — без
    # команды, это только автоматический фолбэк для классификации в "смешанных" чатах).
    for project_key, project in config.CLICKUP_PROJECTS.items():
        if project["command"]:
            app.add_handler(CommandHandler(project["command"], _make_tasks_command_handler(project_key)))
    # Личка — обычный разговор с персоной Marina Twin.
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_message))
    # Группы — тихий сбор переписки, без ответов.
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS, handle_group_message))

    if config.CLICKUP_ENABLED:
        interval = config.CLICKUP_FLUSH_INTERVAL_MINUTES * 60
        app.job_queue.run_repeating(periodic_flush_job, interval=interval, first=interval)
        logger.info(
            "ClickUp-интеграция включена (проекты: %s), автовыгрузка каждые %d мин.",
            ", ".join(config.CLICKUP_LIST_IDS), config.CLICKUP_FLUSH_INTERVAL_MINUTES,
        )
    else:
        logger.info(
            "ClickUp-интеграция выключена (нет CLICKUP_API_TOKEN или ни один CLICKUP_LIST_* не задан) — "
            "сбор задач копится, но никуда не уходит."
        )

    return app


def main() -> None:
    # claude_client уже при импорте выше загрузил базу знаний (см. kb.load_core внутри него)
    logger.info("База загружена, запускаю бота (модель: %s)", config.MODEL_NAME)
    app = build_application()
    app.run_polling()


if __name__ == "__main__":
    main()
