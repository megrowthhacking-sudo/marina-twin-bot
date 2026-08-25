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
import time
from datetime import time as digest_time
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

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


def _detect_project_keyword(text: str) -> str | None:
    """Как _detect_project_binding, но без требования слова "групп-" — для коротких
    прямых ответов на уточняющий вопрос вида "Atlas" или "это Altyn" (см.
    _resolve_classification_reply)."""
    lowered = text.lower()
    for key, project in config.CLICKUP_PROJECTS.items():
        if key == "unsorted":
            continue
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
        storage.update_escalation_after_answer(esc_id, raw_answer=answer_text, posted_text=final_text)
        sent_fail = await update.message.reply_text(
            f"Поняла ответ, но не смогла отправить его в «{group_title}» (возможно, меня там больше нет) — "
            f"перешли, пожалуйста, вручную: {final_text}"
        )
        storage.link_escalation_dm_message(esc_id, sent_fail.message_id)
        return

    storage.update_escalation_after_answer(esc_id, raw_answer=answer_text, posted_text=final_text)
    sent_ok = await update.message.reply_text(f"Готово, ответила в «{group_title}» 👍")
    storage.link_escalation_dm_message(esc_id, sent_ok.message_id)


async def _propose_escalation_correction(update: Update, context: ContextTypes.DEFAULT_TYPE, esc: dict, raw_correction: str) -> None:
    """Владелица тегнула (reply) в личке уже отвеченный вопрос из группы, чтобы его
    исправить или дополнить. В отличие от первого ответа (см. _resolve_escalation),
    здесь не отправляем сразу — показываем черновик (вопрос + прошлый ответ + новая
    правка) и просим подтверждение кнопками, см. handle_escalation_callback. Так можно
    присылать сколько угодно правок подряд — каждая просто перезаписывает предыдущий
    неподтверждённый черновик."""
    esc_id = esc["id"]
    group_title = esc["group_title"]
    asker_name = esc["asker_name"]
    question = esc["question"]
    previous_answer = esc["last_posted_text"] or esc["last_answer"] or ""

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    try:
        addition = escalation.rephrase_correction(group_title, asker_name, question, previous_answer, raw_correction)
    except Exception:
        logger.exception("Не удалось перефразировать правку для эскалации #%s — использую как есть", esc_id)
        addition = raw_correction

    composed = (
        f"Вопрос от {asker_name}: {question}\n\n"
        f"Ранее отвечала: {previous_answer}\n\n"
        f"Уточнение: {addition}"
    )
    storage.set_escalation_draft(esc_id, raw_text=raw_correction, posted_text=composed)

    preview = f"Вот что уйдёт в «{group_title}» как уточнение:\n\n{composed}\n\nОтправляю?"
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Отправить", callback_data=f"esc_confirm:{esc_id}"),
                InlineKeyboardButton("❌ Не отправлять", callback_data=f"esc_cancel:{esc_id}"),
            ]
        ]
    )
    chunks = _split_for_telegram(preview)
    for i, chunk in enumerate(chunks):
        sent_chunk = await update.message.reply_text(chunk, reply_markup=keyboard if i == len(chunks) - 1 else None)
        storage.link_escalation_dm_message(esc_id, sent_chunk.message_id)


async def handle_escalation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатие кнопки "Отправить"/"Не отправлять" под черновиком правки
    (см. _propose_escalation_correction)."""
    query = update.callback_query
    await query.answer()

    if config.OWNER_USER_ID is not None and query.from_user.id != config.OWNER_USER_ID:
        return

    action, _, esc_id_raw = (query.data or "").partition(":")
    try:
        esc_id = int(esc_id_raw)
    except ValueError:
        return

    esc = storage.get_escalation(esc_id)
    if not esc:
        await query.edit_message_text("Не нашла эту эскалацию — возможно, устарела.")
        return

    if action == "esc_cancel":
        storage.clear_escalation_draft(esc_id)
        await query.edit_message_text("Хорошо, не отправляю. Пришли новую правку — ответом на исходный вопрос.")
        return

    if action == "esc_confirm":
        draft_posted = esc.get("draft_posted")
        draft_raw = esc.get("draft_raw")
        if not draft_posted:
            await query.edit_message_text("Этот черновик уже не актуален — пришли уточнение заново.")
            return
        try:
            await context.bot.send_message(chat_id=esc["group_chat_id"], text=draft_posted)
        except Exception:
            logger.exception(
                "Не удалось отправить уточнение в группу %s (эскалация #%s)", esc["group_chat_id"], esc_id
            )
            await query.edit_message_text(
                f"Не смогла отправить в «{esc['group_title']}» (возможно, меня там больше нет) — "
                f"перешли, пожалуйста, вручную:\n\n{draft_posted}"
            )
            return

        storage.update_escalation_after_answer(esc_id, raw_answer=draft_raw, posted_text=draft_posted)
        storage.clear_escalation_draft(esc_id)
        await query.edit_message_text(f"Готово, отправила уточнение в «{esc['group_title']}» 👍")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    text = update.message.text or ""

    if not _is_allowed(user.id):
        logger.warning("Отклонён неразрешённый пользователь %s (%s)", user.id, user.username)
        await update.message.reply_text(
            "Извини, этот бот цифровая копия Марины, он общается в личном чате только с ней."
        )
        return

    # Если пишет владелица — сперва проверяем, не reply ли это на пересланный вопрос из
    # группы (тег исходного сообщения с вопросом в личке). Если да — это либо первый
    # ответ на конкретный (ещё не отвеченный) вопрос, либо правка/дополнение к уже
    # отправленному ответу (см. _propose_escalation_correction) — работает даже если
    # вопросов накопилось несколько, вне очереди FIFO. Иначе, если reply не найден,
    # но есть неотвеченный вопрос вообще — считаем обычным сообщением ответом на самый
    # старый (старое поведение, для простого случая "один вопрос ждёт ответа").
    if config.OWNER_USER_ID is not None and user.id == config.OWNER_USER_ID:
        reply_to = update.message.reply_to_message
        if reply_to:
            esc = storage.get_escalation_by_any_dm_message_id(reply_to.message_id)
            if esc:
                if not esc["resolved"]:
                    pending_tuple = (esc["id"], esc["group_chat_id"], esc["group_title"], esc["asker_name"], esc["question"])
                    await _resolve_escalation(update, context, pending_tuple, text)
                else:
                    await _propose_escalation_correction(update, context, esc, text)
                return
            await update.message.reply_text(
                "Не нашла вопрос, на который вы отвечаете (возможно, устарел). Если "
                "вопросов в очереди несколько — ответьте обычным сообщением (без "
                "reply) на самый старый, либо сделайте reply точно на нужное "
                "пересланное сообщение."
            )
            return
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
    /tasksatlas /tasksaltyn /tasksbs /tasksmisc, либо автоматически по расписанию
    (см. periodic_flush_job) для уже привязанных к проекту чатов, либо (для чатов без
    привязки) классифицируются по проекту индивидуально при автовыгрузке."""
    chat = update.effective_chat
    user = update.effective_user
    text = update.message.text or ""
    if not text.strip():
        return

    # Ответ на уточняющий вопрос "Atlas, Altyn или BestSwift?" (см.
    # _ask_classification_question) — проверяем в первую очередь, это отдельный поток
    # от привязки чата и обращения к "Марине" ниже.
    reply_to = update.message.reply_to_message
    if reply_to:
        classification = storage.get_classification_by_question_message_id(chat.id, reply_to.message_id)
        if classification:
            await _resolve_classification_reply(update, context, classification, text)
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
            esc_id = storage.add_pending_escalation(chat.id, chat.title or str(chat.id), asker_name, text)
            try:
                sent = await context.bot.send_message(
                    chat_id=config.OWNER_USER_ID,
                    text=(
                        f"❓ Вопрос из группы «{chat.title or chat.id}» от {asker_name}:\n\n{text}\n\n"
                        f"Ответь мне сюда обычным сообщением — перескажу это в чат.\n"
                        f"Если позже захочешь поправить или дополнить ответ — сделай reply на это "
                        f"или любое из моих следующих сообщений по этому вопросу, я спрошу "
                        f"подтверждение перед отправкой. Так можно сколько угодно раз."
                    ),
                )
                storage.set_escalation_dm_message_id(esc_id, sent.message_id)
                storage.link_escalation_dm_message(esc_id, sent.message_id)
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
    # Раньше новое сообщение просто копилось в буфере до ближайшей периодической
    # выгрузки (см. periodic_flush_job, CLICKUP_FLUSH_INTERVAL_MINUTES) — из-за этого
    # /urgent и живые отчёты могли не видеть только что написанные задачи. Теперь
    # выгружаем в ClickUp сразу же; periodic_flush_job остаётся как подстраховка на
    # случай, если этот вызов упадёт (сеть, лимиты Claude/ClickUp).
    if config.CLICKUP_ENABLED:
        project_key = storage.get_chat_project(chat.id)
        await _flush_chat_to_clickup(context, chat.id, chat.title or str(chat.id), project_key)


def _create_and_log_task(
    chat_id: int, chat_title: str, project_key: str, title: str, description: str, priority
) -> str | None:
    """Создаёт одну задачу в ClickUp-списке project_key и логирует её в pushed_tasks
    (нужно и для отладки, и для отчёта по /tasksX — см. _send_project_report).
    Возвращает id созданной задачи в ClickUp, либо None при неудаче (список не
    настроен или ClickUp отказал)."""
    list_id = config.CLICKUP_LIST_IDS.get(project_key)
    if not list_id:
        return None
    try:
        result = clickup_client.create_task(list_id, name=title, description=description or "", priority=priority)
        task_id = str(result.get("id", ""))
        storage.log_pushed_task(chat_id, chat_title, task_id, title, project_key)
        return task_id
    except Exception:
        logger.exception("Не удалось создать задачу в ClickUp: %s", title)
        return None


def _push_tasks(chat_id: int, chat_title: str, tasks: list[dict], project_for: callable) -> int:
    """Общая часть: создаёт в ClickUp каждую задачу из tasks под проектом project_for(t).
    Возвращает число реально созданных задач."""
    created = 0
    for t in tasks:
        title = (t.get("title") or "").strip()
        if not title:
            continue
        project_key = project_for(t)
        if not project_key:
            continue
        if _create_and_log_task(chat_id, chat_title, project_key, title, t.get("description", ""), t.get("priority")):
            created += 1
    return created


async def _ask_classification_question(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int, chat_title: str, classification_id: int, task_title: str
) -> None:
    """Задаёт в "смешанном" чате уточняющий вопрос по задаче, которую Claude не смог
    однозначно классифицировать (см. _flush_chat_to_clickup). Ответ (reply на это
    сообщение) ловит handle_group_message → _resolve_classification_reply."""
    text = (
        f"Не поняла, к какому проекту отнести задачу: «{task_title}»\n"
        f"Это Atlas, Altyn или BestSwift? Ответь (reply) на это сообщение названием проекта.\n"
        f"Если никто не подскажет — через некоторое время сама положу в «Разобрать»."
    )
    try:
        sent = await context.bot.send_message(chat_id=chat_id, text=text)
        storage.set_classification_question_message_id(classification_id, sent.message_id)
    except Exception:
        logger.exception(
            "Не удалось задать уточняющий вопрос по классификации #%s в чате %s (%s)",
            classification_id, chat_id, chat_title,
        )


async def _resolve_classification_reply(
    update: Update, context: ContextTypes.DEFAULT_TYPE, classification: dict, reply_text: str
) -> None:
    """Кто-то в группе ответил (reply) на уточняющий вопрос про проект задачи.
    Отвечают Atlas/Altyn/BestSwift — кладём туда; отвечают что-то другое (или
    непонятное) — сразу в "Разобрать", ждать дальше уже не имеет смысла, раз ответ
    уже пришёл."""
    classification_id = classification["id"]
    project_key = _detect_project_keyword(reply_text) or "unsorted"
    label = config.CLICKUP_PROJECTS[project_key]["label"]

    task_id = _create_and_log_task(
        classification["chat_id"],
        classification["chat_title"],
        project_key,
        classification["task_title"],
        classification["task_description"],
        classification["task_priority"],
    )
    storage.resolve_classification(classification_id, project_key)

    if task_id:
        await update.message.reply_text(f"Поняла, добавила «{classification['task_title']}» в «{label}» 👍")
    else:
        await update.message.reply_text(
            f"Поняла (проект «{label}»), но не смогла создать задачу в ClickUp — возможно, список ещё не настроен."
        )


async def _sweep_stale_classifications(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Классификации, на которые никто не ответил дольше
    CLICKUP_CLASSIFICATION_TIMEOUT_MINUTES, — принудительно кладём в "Разобрать", чтобы
    задача не зависла в подвешенном состоянии навсегда."""
    cutoff = time.time() - config.CLICKUP_CLASSIFICATION_TIMEOUT_MINUTES * 60
    for c in storage.get_unresolved_classifications_older_than(cutoff):
        label = config.CLICKUP_PROJECTS["unsorted"]["label"]
        task_id = _create_and_log_task(
            c["chat_id"], c["chat_title"], "unsorted", c["task_title"], c["task_description"], c["task_priority"]
        )
        storage.resolve_classification(c["id"], "unsorted")
        if task_id:
            try:
                await context.bot.send_message(
                    chat_id=c["chat_id"],
                    text=f"Не дождалась ответа — положила «{c['task_title']}» в «{label}» 👍",
                )
            except Exception:
                logger.exception(
                    "Не удалось уведомить чат %s о таймауте классификации #%s", c["chat_id"], c["id"]
                )


async def _flush_chat_to_clickup(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int, chat_title: str, project_key: str | None
) -> int:
    """Извлекает задачи из накопленных сообщений одного чата и пушит их в ClickUp.
    Возвращает число созданных задач.

    Буфер помечается прочитанным ТОЛЬКО если вызов Claude отработал (успешно или с
    пустым результатом) — если сам вызов извлечения упал (сеть, лимиты, кончился
    баланс на Anthropic API и т.п.), сообщения остаются непрочитанными и попробуем
    ещё раз на следующей выгрузке, а не теряем их молча. А вот если сам ClickUp
    отказал при создании конкретной задачи (см. _push_tasks) — это уже не повод
    держать буфер вечно, тут по-прежнему помечаем прочитанным.

    project_key задан → чат закреплён за одним проектом, все задачи туда, без
    классификации. project_key is None → "смешанный" чат без привязки: каждая задача
    классифицируется отдельно (Atlas/Алтын/BestSwift); неоднозначные не падают молча
    в "Разобрать", а сначала переспрашиваются в чате (см. _ask_classification_question)."""
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
            logger.exception(
                "Ошибка извлечения задач для чата %s (%s) — оставляю буфер непрочитанным, попробую ещё раз",
                chat_id, chat_title,
            )
            return 0
        created = _push_tasks(chat_id, chat_title, tasks, lambda _t: project_key)
    else:
        try:
            tasks = task_extractor.extract_tasks_classified(chat_title, rows)
        except Exception:
            logger.exception(
                "Ошибка извлечения/классификации задач для чата %s (%s) — оставляю буфер непрочитанным, попробую ещё раз",
                chat_id, chat_title,
            )
            return 0

        clear_tasks = [t for t in tasks if t.get("project") in ("atlas", "altyn", "bestswift")]
        ambiguous_tasks = [t for t in tasks if t not in clear_tasks]

        created = _push_tasks(chat_id, chat_title, clear_tasks, lambda t: t.get("project"))

        for t in ambiguous_tasks:
            title = (t.get("title") or "").strip()
            if not title:
                continue
            classification_id = storage.add_pending_classification(
                chat_id, chat_title, title, t.get("description", ""), t.get("priority")
            )
            await _ask_classification_question(context, chat_id, chat_title, classification_id, title)

    storage.mark_flushed(chat_id)
    return created


_URGENT_PRIORITIES = {"urgent", "high"}


def _is_urgent(task: dict) -> bool:
    return (task.get("priority") or "") in _URGENT_PRIORITIES


def _format_task_lines(tasks: list[dict]) -> list[str]:
    """Форматирует список задач ClickUp (см. clickup_client.get_open_tasks) в пронумерованные
    строки отчёта, отмечая срочные/высокоприоритетные задачи значком 🔴."""
    lines = []
    for i, t in enumerate(tasks, start=1):
        marker = "🔴 " if _is_urgent(t) else ""
        lines.append(f"{i}. {marker}{t['name']}")
    return lines


async def _fetch_project_tasks(project_key: str) -> list[dict] | None:
    """Общий помощник: тянет живые открытые задачи проекта прямо из ClickUp (см.
    clickup_client.get_open_tasks) — источник истины для всех отчётов (/tasksX,
    /urgent, утренний дайджест). Возвращает None при ошибке сети/API — не поднимает
    исключение дальше, вызывающий код сам решает, как об этом сообщить."""
    list_id = config.CLICKUP_LIST_IDS.get(project_key)
    if not list_id:
        return []
    try:
        return clickup_client.get_open_tasks(list_id)
    except Exception:
        logger.exception("Не удалось получить задачи проекта %s из ClickUp", project_key)
        return None


async def _send_project_report(context: ContextTypes.DEFAULT_TYPE, project_key: str) -> None:
    """Шлёт владелице в личку полный пронумерованный список ОТКРЫТЫХ задач проекта —
    тянет их живьём из ClickUp (не из локального журнала когда-либо созданных ботом
    задач), так отчёт отражает актуальное состояние, включая то, что закрыли или
    поменяли напрямую в ClickUp. Срочные задачи (priority urgent/high) помечены 🔴.
    Вызывается и после команды /tasksX, и утренним дайджестом (см. daily_digest_job)."""
    if config.OWNER_USER_ID is None:
        return
    label = config.CLICKUP_PROJECTS[project_key]["label"]
    tasks = await _fetch_project_tasks(project_key)
    if tasks is None:
        text = f"Не смогла получить задачи «{label}» из ClickUp — попробую в следующий раз."
    elif not tasks:
        text = f"📋 «{label}» — открытых задач сейчас нет."
    else:
        text = "\n".join([f"📋 «{label}» — открытые задачи ({len(tasks)}):"] + _format_task_lines(tasks))
    try:
        for chunk in _split_for_telegram(text):
            await context.bot.send_message(chat_id=config.OWNER_USER_ID, text=chunk)
    except Exception:
        logger.exception("Не удалось отправить отчёт по проекту %s владелице", project_key)


async def _send_urgent_report(context: ContextTypes.DEFAULT_TYPE) -> None:
    """/urgent — по каждому проекту тянет живые задачи из ClickUp, оставляет только
    срочные (priority urgent/high) и собирает одним сообщением с разделом на каждый
    проект (см. _split_for_telegram — режется на несколько сообщений, если не
    помещается в лимит Telegram)."""
    if config.OWNER_USER_ID is None:
        return
    sections = []
    for project_key, project in config.CLICKUP_PROJECTS.items():
        label = project["label"]
        tasks = await _fetch_project_tasks(project_key)
        if tasks is None:
            sections.append(f"«{label}»: не смогла получить задачи из ClickUp.")
            continue
        urgent = [t for t in tasks if _is_urgent(t)]
        if not urgent:
            sections.append(f"«{label}»: срочных задач нет.")
        else:
            sections.append("\n".join([f"🔴 «{label}» — срочные ({len(urgent)}):"] + _format_task_lines(urgent)))
    text = "\n\n".join(sections)
    try:
        for chunk in _split_for_telegram(text):
            await context.bot.send_message(chat_id=config.OWNER_USER_ID, text=chunk)
    except Exception:
        logger.exception("Не удалось отправить сводку срочных задач владелице")


async def handle_urgent_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/urgent — только в личке, только для владелицы: сразу присылает сводку срочных
    задач по всем проектам (см. _send_urgent_report)."""
    chat = update.effective_chat
    if chat.type != "private":
        await update.message.reply_text("Эта команда работает только в личке.")
        return
    if config.OWNER_USER_ID is None or update.effective_user.id != config.OWNER_USER_ID:
        await update.message.reply_text("Эта команда только для владелицы.")
        return
    await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)
    await _send_urgent_report(context)


async def _send_tasksall_report(context: ContextTypes.DEFAULT_TYPE) -> str:
    """/tasksall — по каждому проекту (в порядке config.CLICKUP_PROJECTS) тянет живые
    открытые задачи из ClickUp и собирает единый отчёт с разделом на каждый проект,
    нумерация задач своя в каждом разделе (1-N), срочные помечены 🔴 (см.
    _format_task_lines). Возвращает готовый текст — разбивку под лимит Telegram и
    отправку делает вызывающий код (см. handle_tasksall_command)."""
    sections = []
    for project_key, project in config.CLICKUP_PROJECTS.items():
        label = project["label"]
        list_id = config.CLICKUP_LIST_IDS.get(project_key)
        if not list_id:
            sections.append(f"📋 «{label}»: не настроено.")
            continue
        tasks = await _fetch_project_tasks(project_key)
        if tasks is None:
            sections.append(f"📋 «{label}»: не смогла получить задачи из ClickUp.")
        elif not tasks:
            sections.append(f"📋 «{label}»: нет задач.")
        else:
            sections.append(
                "\n".join([f"📋 «{label}» — открытые задачи ({len(tasks)}):"] + _format_task_lines(tasks))
            )
    return "\n\n".join(sections)


async def handle_tasksall_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/tasksall — только в личке, только для владелицы: присылает открытые задачи
    сразу по всем четырём проектам одним отчётом, с разделом на каждый проект (см.
    _build_tasksall_report)."""
    chat = update.effective_chat
    if chat.type != "private":
        await update.message.reply_text("Эта команда работает только в личке.")
        return
    if config.OWNER_USER_ID is None or update.effective_user.id != config.OWNER_USER_ID:
        await update.message.reply_text("Эта команда только для владелицы.")
        return
    await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)
    text = await _send_tasksall_report(context)
    for chunk in _split_for_telegram(text):
        await context.bot.send_message(chat_id=config.OWNER_USER_ID, text=chunk)


async def daily_digest_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Утренний дайджест (время/часовой пояс — DAILY_DIGEST_HOUR/DAILY_DIGEST_MINUTE/
    MARINATWIN_TIMEZONE в config.py): по каждому проекту шлёт владелице отдельным
    сообщением полный список открытых задач, живьём из ClickUp, срочные помечены 🔴
    (см. _send_project_report)."""
    if not config.CLICKUP_ENABLED or config.OWNER_USER_ID is None:
        return
    for project_key in config.CLICKUP_PROJECTS:
        await _send_project_report(context, project_key)


def _make_tasks_command_handler(project_key: str):
    """Команды /tasksatlas /tasksaltyn /tasksbs /tasksmisc — каждая для своего проекта.
    Вызов команды в чате: (1) немедленно выгружает накопленные задачи чата в список
    этого проекта, (2) закрепляет проект за чатом, чтобы дальше периодическая
    автовыгрузка (см. periodic_flush_job) сама знала, куда слать задачи из этого чата,
    без повторного вызова команды каждый раз, (3) шлёт владелице в личку полный
    пронумерованный список всех задач этого проекта (см. _send_project_report) — в
    сам групповой чат полный список не публикуется."""
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
        created = await _flush_chat_to_clickup(context, chat.id, chat.title or str(chat.id), project_key)
        if created:
            await update.message.reply_text(f"Готово, добавила {created} задач(и) в ClickUp ({label}) 👍")
        else:
            await update.message.reply_text(f"Новых задач в переписке с прошлого раза не нашла (проект «{label}»).")
        await _send_project_report(context, project_key)

    return handler


async def periodic_flush_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Фоновая выгрузка задач по расписанию (CLICKUP_FLUSH_INTERVAL_MINUTES), без
    ручной команды — для ВСЕХ чатов с непрочитанными сообщениями. Для чатов,
    закреплённых за проектом, задачи идут в его список; для "смешанных" чатов без
    привязки — классифицируются по отдельности (см. _flush_chat_to_clickup). Заодно
    подчищает зависшие без ответа уточнения по классификации (см.
    _sweep_stale_classifications)."""
    if not config.CLICKUP_ENABLED:
        return
    for chat_id, chat_title in storage.get_chats_with_pending():
        project_key = storage.get_chat_project(chat_id)
        created = await _flush_chat_to_clickup(context, chat_id, chat_title, project_key)
        if created:
            logger.info(
                "Авто-выгрузка: чат «%s» (%s), проект %s → %d задач в ClickUp",
                chat_title, chat_id, project_key or "не закреплён (классификация)", created,
            )
    await _sweep_stale_classifications(context)


def build_application() -> Application:
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("reset", handle_reset))
    # /urgent — только в личке, только владелице: живая сводка срочных задач по всем
    # проектам сразу (см. handle_urgent_command / _send_urgent_report).
    app.add_handler(CommandHandler("urgent", handle_urgent_command))
    # /tasksall — только в личке, только владелице: живой отчёт по открытым задачам
    # сразу всех четырёх проектов одним сообщением (см. handle_tasksall_command).
    app.add_handler(CommandHandler("tasksall", handle_tasksall_command))
    # По команде на проект: /tasksatlas /tasksaltyn /tasksbs /tasksmisc. "unsorted"/Разобрать
    # теперь тоже привязывается явной командой (/tasksmisc), но по-прежнему остаётся
    # автоматическим фолбэком для классификации задач в "смешанных" чатах.
    for project_key, project in config.CLICKUP_PROJECTS.items():
        if project["command"]:
            app.add_handler(CommandHandler(project["command"], _make_tasks_command_handler(project_key)))
    # Кнопки "Отправить"/"Не отправлять" под черновиком правки к эскалации.
    app.add_handler(CallbackQueryHandler(handle_escalation_callback, pattern=r"^esc_(confirm|cancel):"))
    # Личка — обычный разговор с персоной Marina Twin.
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_message))
    # Группы — тихий сбор переписки, без ответов.
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS, handle_group_message))

    if config.CLICKUP_ENABLED:
        interval = config.CLICKUP_FLUSH_INTERVAL_MINUTES * 60
        app.job_queue.run_repeating(periodic_flush_job, interval=interval, first=interval)
        digest_msg = ""
        if config.OWNER_USER_ID is not None:
            app.job_queue.run_daily(
                daily_digest_job,
                time=digest_time(
                    hour=config.DAILY_DIGEST_HOUR,
                    minute=config.DAILY_DIGEST_MINUTE,
                    tzinfo=ZoneInfo(config.MARINATWIN_TIMEZONE),
                ),
            )
            digest_msg = (
                f", утренний дайджест в {config.DAILY_DIGEST_HOUR:02d}:{config.DAILY_DIGEST_MINUTE:02d} "
                f"({config.MARINATWIN_TIMEZONE})"
            )
        logger.info(
            "ClickUp-интеграция включена (проекты: %s), автовыгрузка каждые %d мин%s.",
            ", ".join(config.CLICKUP_LIST_IDS), config.CLICKUP_FLUSH_INTERVAL_MINUTES, digest_msg,
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
