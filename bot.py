"""
Telegram-бот "Marina Twin" — штатный юрист по праву РФ, ВЭД и крипто
в СНГ/Таможенном союзе/ЕАЭС. Интерфейс поверх Claude API с кэшированной базой
знаний и точечной подгрузкой странового модуля по ходу разговора.

Запуск: python bot.py
Нужны переменные окружения: TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY (см. .env.example).
"""

import asyncio
import logging
import re
import time
from datetime import datetime, time as digest_time, timedelta
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.error import BadRequest, RetryAfter
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import altyn_registry
import calendar_client
import chat_memory
import claude_client
import clickup_client
import config
import escalation
import kb
import meeting_extractor
import schedule_reminders
import storage
import task_command
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


# {telegram_username_в_нижнем_регистре: employee_key, ...} — построено один раз из
# config.EMPLOYEE_COMMANDS[...]["telegram_username"] (часть 30, по прямой просьбе
# владелицы: она прислала @username шести сотрудников, а не числовой telegram_user_id —
# см. _maybe_capture_employee_telegram_id ниже, где это используется для автоматического
# распознавания).
_EMPLOYEE_USERNAME_TO_KEY = {
    employee["telegram_username"].lower(): key
    for key, employee in config.EMPLOYEE_COMMANDS.items()
    if employee.get("telegram_username")
}


def _maybe_capture_employee_telegram_id(update: Update) -> None:
    """Подглядывает @username в КАЖДОМ сообщении, которое бот и так получает (личка и
    группы — см. вызовы в handle_start/handle_message/handle_group_message), и если он
    совпадает (без учёта регистра) с одним из config.EMPLOYEE_COMMANDS[...]
    ["telegram_username"] — сохраняет настоящий telegram_user_id этого сотрудника в
    storage (см. storage.save_employee_telegram_id), после чего кнопка "➡️ Переслать"
    (см. _resolve_employee_telegram_id/_available_forward_recipients) сама начинает
    работать для него, без нового деплоя. По прямой просьбе владелицы, часть 30: она
    прислала @username сотрудников, а не числовой id — Telegram не даёт боту написать
    первым тому, кто ему никогда не писал, поэтому нужен именно этот обходной путь,
    а не мгновенная настройка. Тихая операция — ничего не отвечает и не может сломать
    обычную обработку сообщения, вызывается "между делом", в начале обработчика."""
    user = update.effective_user
    if user is None or not user.username:
        return
    employee_key = _EMPLOYEE_USERNAME_TO_KEY.get(user.username.lower())
    if not employee_key:
        return
    if storage.get_employee_telegram_id(employee_key) == user.id:
        return  # уже сохранён этот же id — не дёргаем базу заново на каждое сообщение
    try:
        storage.save_employee_telegram_id(employee_key, user.id, user.username)
        logger.info(
            "Распознан telegram_user_id сотрудника «%s» по @%s — пересылка теперь доступна",
            config.EMPLOYEE_COMMANDS[employee_key]["label"],
            user.username,
        )
    except Exception:
        logger.exception("Не удалось сохранить telegram_user_id для %s (@%s)", employee_key, user.username)


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
        # Разговор явно "вернулся" к России — сбрасываем остальные страны, но RUSSIA
        # теперь сам по себе подключаемый модуль (не часть core), так что явно
        # включаем именно его, а не пустой список.
        return ["RUSSIA"]
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

_MARINA_NAME_RE = re.compile(r"\bмарин(а|ы|е|у|ой|ою)\b|\bmar[iy]na\b|\bmary\b", re.IGNORECASE)

# Кэш @username живой владелицы (для распознавания обращений вида "@её_ник ..." в
# группе — отдельно от @username самого бота). None до первой попытки резолва;
# _owner_username_resolved отличает "ещё не пробовали" от "пробовали, не вышло" —
# чтобы не долбить Telegram API на каждое сообщение при ошибке.
_owner_username_cache: str | None = None
_owner_username_resolved = False


async def _get_owner_username(context: ContextTypes.DEFAULT_TYPE) -> str | None:
    """Резолвит и кэширует @username живой Марины (config.OWNER_USER_ID) через Telegram
    API — один раз за время жизни процесса (username меняется крайне редко). Нужен,
    чтобы обращение в группе по её личному тегу (не тегу бота) тоже ловилось как
    вопрос к ней. При ошибке — тихо None, не роняем обработку сообщения."""
    global _owner_username_cache, _owner_username_resolved
    if _owner_username_resolved:
        return _owner_username_cache
    _owner_username_resolved = True
    if config.OWNER_USER_ID is None:
        return None
    try:
        chat = await context.bot.get_chat(config.OWNER_USER_ID)
        _owner_username_cache = chat.username
    except Exception:
        logger.exception(
            "Не удалось получить username владелицы (user_id=%s) для распознавания обращений",
            config.OWNER_USER_ID,
        )
    return _owner_username_cache


async def _is_addressed_to_marina(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    bot_username = context.bot.username
    if bot_username and f"@{bot_username.lower()}" in text.lower():
        return True
    owner_username = await _get_owner_username(context)
    if owner_username and f"@{owner_username.lower()}" in text.lower():
        return True
    reply_to = update.message.reply_to_message
    if reply_to and reply_to.from_user and reply_to.from_user.id == context.bot.id:
        return True
    return bool(_MARINA_NAME_RE.search(text))


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _maybe_capture_employee_telegram_id(update)
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


async def _send_draft_with_buttons(context, esc_id: int, preview_text: str, keyboard) -> None:
    chunks = _split_for_telegram(preview_text)
    for i, chunk in enumerate(chunks):
        sent = await context.bot.send_message(
            chat_id=config.OWNER_USER_ID, text=chunk, reply_markup=keyboard if i == len(chunks) - 1 else None
        )
        storage.link_escalation_dm_message(esc_id, sent.message_id)


def _format_mention(asker_name: str | None, asker_username: str | None) -> str:
    """Единый формат обращения к автору вопроса — используется и в финальном сообщении,
    отправляемом в группу, и в черновике на согласование в личке, чтобы владелица видела
    заранее именно то, что уйдёт в чат. Раньше было либо/либо (юзернейм ИЛИ имя) — теряли
    либо узнаваемость по имени, либо кликабельный тег; теперь показываем оба, если тег
    известен."""
    name = (asker_name or "").strip()
    username = (asker_username or "").strip()
    if name and username:
        return f"{name} (@{username}), "
    if username:
        return f"@{username} "
    if name:
        return f"{name}, "
    return ""


def _strip_marina_trigger(text: str, bot_username: str | None, owner_username: str | None) -> str:
    """Убирает из текста упоминание/тег/имя, которыми обратились к Марине — остаток
    показывает, есть ли у самого тег-сообщения собственный текст вопроса, или это голый
    тег (см. _extract_question_context)."""
    stripped = text
    if bot_username:
        stripped = re.sub(re.escape(f"@{bot_username}"), "", stripped, flags=re.IGNORECASE)
    if owner_username:
        stripped = re.sub(re.escape(f"@{owner_username}"), "", stripped, flags=re.IGNORECASE)
    stripped = _MARINA_NAME_RE.sub("", stripped)
    return stripped.strip(" ,.!?:;\n-—")


async def _extract_question_context(update: Update, context: ContextTypes.DEFAULT_TYPE, chat, msg, text: str) -> str:
    """Обращение к Марине не всегда содержит сам вопрос — иногда коллега сначала пишет
    вопрос отдельным сообщением, а к Марине обращается уже следующим, коротким ("Марина?",
    просто тег без своего текста). Раньше в этом случае эскалация уходила с текстом самого
    тег-сообщения, и владелица получала в личке вопрос без содержания. Теперь: если
    тег-сообщение — reply на чьё-то ещё сообщение (не на сообщение самого бота), вопрос
    берём оттуда; если это не reply, но у тег-сообщения почти нет своего текста — берём
    последнее недавнее сообщение чата (см. storage.get_last_group_message). Если у
    тег-сообщения есть содержательный текст — используем его как раньше."""
    bot_username = context.bot.username
    owner_username = await _get_owner_username(context)
    remainder = _strip_marina_trigger(text, bot_username, owner_username)
    reply_to = msg.reply_to_message
    if reply_to and not (reply_to.from_user and reply_to.from_user.id == context.bot.id):
        reply_text = (reply_to.text or reply_to.caption or "").strip()
        if reply_text:
            return f"{reply_text}\n\n{remainder}" if remainder else reply_text
    if not remainder:
        recent = storage.get_last_group_message(chat.id)
        if recent and (recent.get("text") or "").strip():
            return recent["text"].strip()
    return text


def _initial_draft_keyboard(esc_id: int):
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("✅ Подтверждаю", callback_data=f"esc_confirm:{esc_id}"),
            InlineKeyboardButton("❌ Не подтверждаю", callback_data=f"esc_cancel:{esc_id}"),
        ]]
    )


async def _propose_initial_draft(
    context,
    esc_id: int,
    group_title: str,
    asker_name: str,
    question: str,
    project_key: str | None = None,
    asker_username: str | None = None,
    chat_id: int | None = None,
) -> None:
    # "Память" чата (по прямой просьбе владелицы, 06.09) — сжатая сводка более ранней
    # переписки этого группового чата, если она уже накоплена (см. chat_memory.py,
    # periodic_memory_job ниже); лучшим усилием — если чат неизвестен (chat_id не
    # передали, например esc_retry ниже) или памяти ещё нет, просто продолжаем без неё.
    chat_summary = chat_memory.get_summary_for_draft(chat_id) if chat_id is not None else None
    try:
        draft = escalation.draft_initial_answer(
            group_title, asker_name, question, project_key, chat_summary=chat_summary
        )
    except Exception:
        logger.exception("Не удалось составить черновик ответа для эскалации #%s", esc_id)
        draft = ""

    if not draft:
        storage.set_escalation_flow_stage(esc_id, "awaiting_own_text")
        await context.bot.send_message(
            chat_id=config.OWNER_USER_ID,
            text="Не смогла сама составить черновик — напиши, пожалуйста, ответ своими словами.",
        )
        return

    storage.set_escalation_draft(esc_id, raw_text=draft, posted_text=draft)
    storage.set_escalation_flow_stage(esc_id, "initial_draft")
    mention = _format_mention(asker_name, asker_username)
    preview = f"Предлагаю ответить в «{group_title}»:\n\n{mention}{draft}"
    await _send_draft_with_buttons(context, esc_id, preview, _initial_draft_keyboard(esc_id))


async def _finalize_own_answer(context, esc: dict, raw_text: str) -> None:
    """Марина написала ответ своими словами (после кнопки "✍️ Написать ответ", либо
    ответив на пересланный вопрос сразу своим текстом). В отличие от AI-черновика, её
    собственный текст здесь НЕ переформулируем — он и так от её лица, перефразировка
    только исказила бы то, что она реально хотела сказать. Просто показываем как есть
    и просим подтверждение перед отправкой (см. esc_confirm)."""
    esc_id = esc["id"]
    group_title = esc["group_title"]
    final_text = raw_text

    storage.set_escalation_draft(esc_id, raw_text=raw_text, posted_text=final_text)
    storage.set_escalation_flow_stage(esc_id, "final_draft")
    mention = _format_mention(esc.get("asker_name"), esc.get("asker_username"))
    preview = f"Вот как получилось для «{group_title}»:\n\n{mention}{final_text}"
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("📤 Отправляю", callback_data=f"esc_confirm:{esc_id}"),
            InlineKeyboardButton("🚫 Не отправляю", callback_data=f"esc_cancel:{esc_id}"),
        ]]
    )
    await _send_draft_with_buttons(context, esc_id, preview, keyboard)


_CANCEL_PHRASES = {"отмена", "отмена.", "отмена!"}


async def _handle_owner_escalation_message(update, context, esc: dict, text: str) -> None:
    esc_id = esc["id"]
    if text.strip().lower() in _CANCEL_PHRASES:
        storage.cancel_escalation_flow(esc_id)
        await update.message.reply_text(
            f"Поняла, не вмешиваюсь — вопрос от {esc['asker_name']} из «{esc['group_title']}» оставляю на тебя."
        )
        return

    if not esc["resolved"]:
        await _finalize_own_answer(context, esc, text)
        return
    await _propose_escalation_correction(update, context, esc, text)


async def _send_confirmed_answer(context, query, esc: dict, draft_raw: str, draft_posted: str) -> None:
    """Фактическая отправка подтверждённого ответа в группу — вынесено из esc_confirm
    отдельной функцией, чтобы esc_confirm_anyway мог переиспользовать ту же логику."""
    esc_id = esc["id"]
    mention = _format_mention(esc.get("asker_name"), esc.get("asker_username"))
    text_to_send = f"{mention}{draft_posted}"
    reply_to_message_id = esc.get("group_question_message_id")
    try:
        try:
            await context.bot.send_message(
                chat_id=esc["group_chat_id"], text=text_to_send, reply_to_message_id=reply_to_message_id,
            )
        except BadRequest:
            logger.warning(
                "Не удалось ответить reply-ом на вопрос (message_id=%s, эскалация #%s) — отправляю без reply",
                reply_to_message_id, esc_id,
            )
            await context.bot.send_message(chat_id=esc["group_chat_id"], text=text_to_send)
    except Exception:
        logger.exception(
            "Не удалось отправить уточнение в группу %s (эскалация #%s)", esc["group_chat_id"], esc_id
        )
        await query.edit_message_text(
            f"Не смогла отправить в «{esc['group_title']}» (возможно, меня там больше нет) — "
            f"перешли, пожалуйста, вручную:\n\n{draft_posted}"
        )
        return
    was_resolved = esc["resolved"]
    storage.update_escalation_after_answer(esc_id, raw_answer=draft_raw, posted_text=draft_posted)
    storage.clear_escalation_draft(esc_id)
    if was_resolved:
        await query.edit_message_text(f"Готово, отправила уточнение в «{esc['group_title']}» 👍")
    else:
        await query.edit_message_text(f"Готово, ответила в «{esc['group_title']}» 👍")


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

    if action == "esc_retry":
        await query.edit_message_text("Секунду, предложу другой вариант...")
        chat_summary = chat_memory.get_summary_for_draft(esc["group_chat_id"])
        try:
            draft = escalation.draft_initial_answer(
                esc["group_title"], esc["asker_name"], esc["question"], chat_summary=chat_summary
            )
        except Exception:
            logger.exception("Не удалось составить повторный черновик для эскалации #%s", esc_id)
            draft = ""

        if not draft:
            storage.set_escalation_flow_stage(esc_id, "awaiting_own_text")
            await context.bot.send_message(
                chat_id=config.OWNER_USER_ID,
                text="Не смогла сама составить другой вариант — напиши, пожалуйста, ответ своими словами.",
            )
            return

        storage.set_escalation_draft(esc_id, raw_text=draft, posted_text=draft)
        storage.set_escalation_flow_stage(esc_id, "initial_draft")
        mention = _format_mention(esc.get("asker_name"), esc.get("asker_username"))
        preview = f"Предлагаю ответить в «{esc['group_title']}»:\n\n{mention}{draft}"
        await _send_draft_with_buttons(context, esc_id, preview, _initial_draft_keyboard(esc_id))
        return

    if action == "esc_own":
        storage.set_escalation_flow_stage(esc_id, "awaiting_own_text")
        await query.edit_message_text("Хорошо, жду твой вариант ответа обычным сообщением.")
        return

    if action == "esc_cancel":
        # И "не подтверждаю" AI-черновика (initial_draft), и "не отправляю" собственного
        # текста Марины (final_draft) ведут к одному и тому же выбору — предложить другой
        # вариант или написать самой — и повторяются, пока ответ не будет принят/отправлен.
        # Раньше final_draft вместо кнопок просто просил написать новый текст без выбора —
        # цикл "предложить/написать" там не замыкался.
        if not esc["resolved"] and esc["flow_stage"] in ("initial_draft", "final_draft"):
            storage.set_escalation_flow_stage(esc_id, "reject_choice")
            storage.clear_escalation_draft(esc_id)
            keyboard = InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("🔄 Предложить новый ответ", callback_data=f"esc_retry:{esc_id}"),
                    InlineKeyboardButton("✍️ Написать ответ", callback_data=f"esc_own:{esc_id}"),
                ]]
            )
            await query.edit_message_text(
                "Хорошо, не отправляю этот черновик. Предложить другой вариант, или напишешь сама?",
                reply_markup=keyboard,
            )
            return
        storage.clear_escalation_draft(esc_id)
        await query.edit_message_text("Хорошо, не отправляю. Пришли новую правку — ответом на исходный вопрос.")
        return

    if action == "esc_confirm":
        draft_posted = esc.get("draft_posted")
        draft_raw = esc.get("draft_raw")
        if not draft_posted:
            await query.edit_message_text("Этот черновик уже не актуален — пришли уточнение заново.")
            return
        edited_question = esc.get("edited_question")
        if edited_question and edited_question != esc["question"]:
            keyboard = InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("📤 Всё равно отправляю", callback_data=f"esc_confirm_anyway:{esc_id}"),
                    InlineKeyboardButton("✍️ Напишу новый ответ", callback_data=f"esc_edited_rewrite:{esc_id}"),
                ]]
            )
            await query.edit_message_text(
                f"Стоп — пока согласовывали ответ, вопрос в «{esc['group_title']}» успели отредактировать.\n\n"
                f"Было: {esc['question']}\n\n"
                f"Стало: {edited_question}\n\n"
                f"Подготовленный ответ:\n{draft_posted}\n\n"
                f"Отправить его всё равно, или лучше написать новый под изменённый вопрос?",
                reply_markup=keyboard,
            )
            return
        await _send_confirmed_answer(context, query, esc, draft_raw, draft_posted)
        return
    if action == "esc_confirm_anyway":
        draft_posted = esc.get("draft_posted")
        draft_raw = esc.get("draft_raw")
        if not draft_posted:
            await query.edit_message_text("Этот черновик уже не актуален — пришли уточнение заново.")
            return
        storage.clear_escalation_edited_question(esc_id)
        await _send_confirmed_answer(context, query, esc, draft_raw, draft_posted)
        return
    if action == "esc_edited_rewrite":
        new_question = esc.get("edited_question") or esc["question"]
        storage.update_escalation_question(esc_id, new_question)
        storage.clear_escalation_edited_question(esc_id)
        storage.clear_escalation_draft(esc_id)
        storage.set_escalation_flow_stage(esc_id, "awaiting_own_text")
        await query.edit_message_text(
            f"Хорошо — вопрос теперь звучит так:\n\n{new_question}\n\n"
            f"Напиши, пожалуйста, новый ответ обычным сообщением."
        )
        return


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    text = update.message.text or ""

    _maybe_capture_employee_telegram_id(update)

    if not _is_allowed(user.id):
        logger.warning("Отклонён неразрешённый пользователь %s (%s)", user.id, user.username)
        await update.message.reply_text(
            'Извините, этот бот - цифровая копия Марины, он общается в личном чате только с ней. Если у Вас имеется вопрос к Марине - пишите в нашей с Вами общей группе в одном сообщении: "Марина и далее свой вопрос" или также в одном сообщении: "@marina_ai_twin_bot и далее Ваш вопрос". Спасибо! Мне будет приятно с Вами общаться!'
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
                await _handle_owner_escalation_message(update, context, esc, text)
                return
            await update.message.reply_text(
                "Не нашла вопрос, на который вы отвечаете (возможно, устарел). Если "
                "вопросов в очереди несколько — ответьте обычным сообщением (без "
                "reply) на самый старый, либо сделайте reply точно на нужное "
                "пересланное сообщение."
            )
            return
        # Если владелица нажала "✏️ Изменить" под черновиком встречи (см.
        # handle_calendar_callback) — следующее её сообщение (даже не reply) нужно
        # перехватить как исправленный текст встречи, а не как обычный разговор с Twin
        # или лог задач/встреч ниже. Проверяется раньше "pending = get_oldest_pending_
        # escalation()", чтобы правка встречи не была случайно принята за ответ на
        # старый висящий вопрос эскалации.
        if config.GOOGLE_CALENDAR_ENABLED:
            awaiting_meeting = storage.get_meeting_awaiting_edit(user.id)
            if awaiting_meeting:
                await _apply_meeting_edit(context, user, awaiting_meeting, text)
                return
        pending = storage.get_oldest_pending_escalation()
        if pending:
            esc = storage.get_escalation(pending[0])
            if esc:
                await _handle_owner_escalation_message(update, context, esc, text)
                return
        # Обычное сообщение владелицы в личке (не reply на эскалацию) — сперва проверяем,
        # не явная ли это осознанная команда поставить задачу в конкретный список/статус
        # (см. _propose_explicit_task_command, по прямой просьбе владелицы, 06.09) — если
        # да, обычное фоновое логирование (_log_owner_dm_tasks) для этого же сообщения уже
        # не запускаем (иначе задача задвоится). Плюс, независимо от этого, проверяем, не
        # похоже ли сообщение на просьбу поставить встречу (см. _propose_meeting_draft).
        # Только для самой владелицы: у остальных пользователей в личке — просто разговор
        # с Twin, их сообщения в ClickUp/календарь не идут.
        handled_as_task_command = await _propose_explicit_task_command(context, user, text)
        if not handled_as_task_command:
            await _log_owner_dm_tasks(user, text)
        await _propose_meeting_draft(context, user, text)

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


async def _handle_group_message_edited(chat, msg, text: str) -> None:
    """Пользователь отредактировал своё сообщение в группе. Проверяем, не относится ли
    отредактированное сообщение к вопросу, который сейчас в процессе эскалации — если да,
    запоминаем новый текст, чтобы esc_confirm предупредил владелицу перед отправкой
    (см. handle_escalation_callback). Иначе игнорируем. Раньше правки сообщений доходили
    до этого же MessageHandler'а (filters.TEXT матчит и edited_message) и падали
    необработанным AttributeError на update.message.text, т.к. update.message для
    edited-апдейта всегда None (правильное поле — update.effective_message)."""
    esc = storage.get_escalation_by_group_message_id(chat.id, msg.message_id)
    if not esc:
        return
    if text == esc["question"]:
        storage.clear_escalation_edited_question(esc["id"])
        return
    storage.set_escalation_edited_question(esc["id"], text)
    logger.info(
        "Вопрос эскалации #%s отредактирован в группе %s — запомнила новый текст", esc["id"], chat.id
    )


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """В групповых чатах Marina Twin по умолчанию молча слушает и копит переписку —
    не отвечает, не участвует в разговоре. Три исключения:
    (1) сообщение закрепляет чат за проектом ("эта группа про задачи Altyn") —
    отвечает подтверждением;
    (2) к ней явно обращаются (@упоминание, reply на её сообщение, имя "Марина") —
    молча (без плейсхолдера в самом чате — раньше был "секунду, уточню и вернусь",
    но это раздражало коллег) пересылает вопрос владелице в личку с черновиком ответа
    на кнопках (см. _propose_initial_draft); в группе появится что-то, только когда
    Марина подтвердит ответ в личке (см. handle_escalation_callback/esc_confirm);
    (3) кто-то отредактировал уже написанное сообщение — см. _handle_group_message_edited.
    Иначе сообщение просто уходит в буфер — задачи из него достаются командой
    /tasksatlas /tasksaltyn /tasksbs /tasksmisc, либо автоматически по расписанию
    (см. periodic_flush_job) для уже привязанных к проекту чатов, либо (для чатов без
    привязки) классифицируются по проекту индивидуально при автовыгрузке."""
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    if msg is None:
        return
    _maybe_capture_employee_telegram_id(update)
    text = msg.text or ""
    if not text.strip():
        return

    if update.edited_message is not None:
        await _handle_group_message_edited(chat, msg, text)
        return

    bound_project = _detect_project_binding(text)
    if bound_project:
        previous_project = storage.get_chat_project(chat.id)
        storage.set_chat_project(chat.id, bound_project)
        if bound_project == "unsorted":
            if previous_project and previous_project != "unsorted":
                prev_label = config.CLICKUP_PROJECTS[previous_project]["label"]
                await msg.reply_text(
                    f"Поняла, переключаю этот чат с проекта «{prev_label}» на «Unsorted» — "
                    f"теперь буду собирать отсюда задачи в папку «Unsorted» 👍"
                )
            else:
                await msg.reply_text("Поняла, буду собирать отсюда задачи в папку «Unsorted» 👍")
        else:
            label = config.CLICKUP_PROJECTS[bound_project]["label"]
            if previous_project and previous_project != bound_project:
                prev_label = (
                    "Unsorted" if previous_project == "unsorted"
                    else config.CLICKUP_PROJECTS[previous_project]["label"]
                )
                await msg.reply_text(
                    f"Поняла, переключаю этот чат с проекта «{prev_label}» на «{label}» — "
                    f"теперь буду собирать здесь задачи по проекту «{label}» 👍"
                )
            else:
                await msg.reply_text(f"Поняла, буду собирать здесь задачи по проекту «{label}» 👍")
        return

    if await _is_addressed_to_marina(update, context, text):
        if config.OWNER_USER_ID is not None:
            # Раньше здесь был плейсхолдер в саму группу ("Секунду, уточню и вернусь") —
            # убрали: коллег раздражало, что бот вообще что-то говорит в чате прежде,
            # чем Марина реально ответила. Теперь в группе тихо, пока не подтверждён
            # финальный ответ (см. esc_confirm в handle_escalation_callback).
            # Вопрос не всегда лежит в самом тег-сообщении — иногда коллега сначала пишет
            # вопрос, а к Марине обращается уже следующим, коротким сообщением (см.
            # _extract_question_context). question_text — то, что реально пойдёт как текст
            # вопроса; text (сырое тег-сообщение) по-прежнему используем только для
            # group_question_message_id/reply-threading ниже.
            question_text = await _extract_question_context(update, context, chat, msg, text)
            asker_name = (user.first_name or user.username or "коллега") if user else "коллега"
            asker_username = user.username if user else None
            group_title = chat.title or str(chat.id)
            esc_id = storage.add_pending_escalation(
                chat.id,
                group_title,
                asker_name,
                question_text,
                group_question_message_id=msg.message_id,
                asker_user_id=user.id if user else None,
                asker_username=asker_username,
            )
            try:
                mention = _format_mention(asker_name, asker_username)
                sent = await context.bot.send_message(
                    chat_id=config.OWNER_USER_ID,
                    text=f"❓ Вопрос из группы «{group_title}» от {mention.rstrip(', ')}:\n\n{question_text}",
                )
                storage.set_escalation_dm_message_id(esc_id, sent.message_id)
                storage.link_escalation_dm_message(esc_id, sent.message_id)
            except Exception:
                logger.exception("Не удалось отправить эскалацию владелице (user_id=%s)", config.OWNER_USER_ID)
                return
            project_key = storage.get_chat_project(chat.id)
            await _propose_initial_draft(
                context, esc_id, group_title, asker_name, question_text, project_key, asker_username, chat.id
            )
            return
        logger.warning(
            "Обращение к Марине в чате %s, но MARINATWIN_OWNER_USER_ID не настроен — "
            "эскалация выключена, сообщение уйдёт в обычный сбор задач.",
            chat.id,
        )

    user_name = (user.first_name or user.username or "кто-то") if user else "кто-то"
    storage.add_group_message(
        chat.id, chat.title or str(chat.id), user_name, text,
        telegram_username=(user.username if user else None),
    )
    # Раньше новое сообщение просто копилось в буфере до ближайшей периодической
    # выгрузки (см. periodic_flush_job, CLICKUP_FLUSH_INTERVAL_MINUTES) — из-за этого
    # /urgent и живые отчёты могли не видеть только что написанные задачи. Теперь
    # выгружаем в ClickUp сразу же; periodic_flush_job остаётся как подстраховка на
    # случай, если этот вызов упадёт (сеть, лимиты Claude/ClickUp).
    if config.CLICKUP_ENABLED:
        project_key = storage.get_chat_project(chat.id)
        await _flush_chat_to_clickup(context, chat.id, chat.title or str(chat.id), project_key)



def _resolve_assignee_id(name: str | None) -> int | None:
    """Пытается сопоставить имя ответственного (как его назвал Claude в task_extractor.py,
    поле assignee_name) с ClickUp user_id по config.CLICKUP_ASSIGNEE_MAP. Осознанно строгое
    сравнение (без нечётких совпадений) — лучше не проставить Assignee, чем назначить не
    тому человеку. Пусто/нет совпадения — None, вызывающий код просто не передаёт assignees."""
    if not name:
        return None
    return config.CLICKUP_ASSIGNEE_MAP.get(name.strip().lower())


def _resolve_task_target(name: str | None) -> tuple[str, dict] | None:
    """Сопоставляет названный владелицей список/пространство (например "WEEKLY", "Атлас",
    как его вернул task_command.extract_task_command в поле target_name) с одним из
    config.CLICKUP_TASK_TARGETS — по точному совпадению с ключом/label или по тем же
    ключевым словам, что использует kb.detect для автоматической классификации чатов по
    проекту (см. config.CLICKUP_PROJECTS), плюс отдельная запись "weekly" для списка
    WEEKLY TASKS (config.CLICKUP_LIST_WEEKLY). None, если название не удалось сопоставить
    ни с одним известным списком — тогда _propose_explicit_task_command прямо спросит
    владелицу уточнить, а не будет гадать."""
    if not name:
        return None
    lowered = name.strip().lower()
    if not lowered:
        return None
    for key, target in config.CLICKUP_TASK_TARGETS.items():
        if lowered == key or lowered == target["label"].lower():
            return key, target
    for key, target in config.CLICKUP_TASK_TARGETS.items():
        if any(kw in lowered for kw in target["keywords"]):
            return key, target
    return None


def _resolve_task_status(list_id: str, status_name_raw: str) -> tuple[str | None, list[str]]:
    """Сверяет названный владелицей статус (например "Понедельник") с реальными статусами
    списка ClickUp (clickup_client.get_list_statuses) — сравнение без учёта регистра,
    потому что в разговоре статус пишется как удобно, а в ClickUp хранится в своём
    регистре. Возвращает (имя_статуса_как_в_ClickUp_или_None, список_всех_статусов) —
    первое None, если статус не назван (status_name_raw пусто — задача создастся с
    дефолтным статусом списка) ИЛИ назван, но не нашёлся среди реальных статусов (тогда
    вызывающий код должен показать владелице второй элемент — реальные варианты — а не
    создавать задачу с выдуманным именем статуса). Может бросить исключение (сеть/API) —
    вызывающий код сам решает, как это показать."""
    statuses = clickup_client.get_list_statuses(list_id)
    if not status_name_raw:
        return None, statuses
    lowered = status_name_raw.strip().lower()
    for s in statuses:
        if s.lower() == lowered:
            return s, statuses
    return None, statuses


def _reporter_lookup_from_rows(rows: list[dict]) -> dict[str, str | None]:
    """По прямой просьбе владелицы, часть 33 ("от кого задача"): строит словарь
    user_name → telegram_username из накопленных сообщений чата (см. storage.get_unflushed/
    task_extractor.extract_tasks — тот же rows), чтобы потом сопоставить "reporter_name",
    которое вернул экстрактор (см. task_extractor.py — берёт имя ТОЧНО как в переписке,
    "Имя: текст"), с настоящим Telegram-ником этого человека. Если один user_name
    встречается несколько раз в буфере — берём username из последнего вхождения (не
    принципиально, обычно один и тот же человек пишет с одним и тем же username)."""
    return {r["user_name"]: r.get("telegram_username") for r in rows if r.get("user_name")}


def _create_and_log_task(
    chat_id: int,
    chat_title: str,
    project_key: str,
    title: str,
    description: str,
    priority,
    assignee_id: int | None = None,
    reporter_name: str | None = None,
    reporter_username: str | None = None,
) -> str | None:
    """Создаёт одну задачу в ClickUp-списке project_key и логирует её в pushed_tasks
    (нужно и для отладки, и для отчёта по /tasksX — см. _send_project_report).
    assignee_id — ClickUp user_id ответственного, если удалось сопоставить (см.
    _resolve_assignee_id), иначе None. reporter_name/reporter_username — по прямой
    просьбе владелицы, часть 33: кто в переписке поднял эту задачу (см.
    _reporter_lookup_from_rows) — просто сохраняются в pushed_tasks, чтобы потом
    показать "от кого" в отчётах (см. _format_task_lines/_format_employee_task_lines),
    не влияют на саму задачу в ClickUp. Возвращает id созданной задачи в ClickUp, либо
    None при неудаче (список не настроен или ClickUp отказал)."""
    list_id = config.CLICKUP_LIST_IDS.get(project_key)
    if not list_id:
        return None
    try:
        result = clickup_client.create_task(
            list_id,
            name=title,
            description=description or "",
            priority=priority,
            assignees=[assignee_id] if assignee_id else None,
        )
        task_id = str(result.get("id", ""))
        storage.log_pushed_task(
            chat_id, chat_title, task_id, title, project_key,
            reporter_name=reporter_name, reporter_username=reporter_username,
        )
        return task_id
    except Exception:
        logger.exception("Не удалось создать задачу в ClickUp: %s", title)
        return None


def _push_tasks(
    chat_id: int,
    chat_title: str,
    tasks: list[dict],
    project_for: callable,
    reporter_lookup: dict[str, str | None] | None = None,
) -> int:
    """Общая часть: создаёт в ClickUp каждую задачу из tasks под проектом project_for(t).
    reporter_lookup (см. _reporter_lookup_from_rows) — сопоставляет "reporter_name" из
    экстрактора с реальным Telegram @username, для "от кого задача" (часть 33); можно не
    передавать, если сопоставлять не с чем (тогда сохранится только reporter_name, без
    username). Возвращает число реально созданных задач."""
    created = 0
    for t in tasks:
        title = (t.get("title") or "").strip()
        if not title:
            continue
        project_key = project_for(t)
        if not project_key:
            continue
        assignee_id = _resolve_assignee_id(t.get("assignee_name"))
        reporter_name = (t.get("reporter_name") or "").strip() or None
        reporter_username = reporter_lookup.get(reporter_name) if reporter_lookup and reporter_name else None
        if _create_and_log_task(
            chat_id, chat_title, project_key, title, t.get("description", ""), t.get("priority"), assignee_id,
            reporter_name=reporter_name, reporter_username=reporter_username,
        ):
            created += 1
    return created


async def _log_owner_dm_tasks(user, text: str) -> None:
    """Марина написала что-то похожее на задачу прямо в личке боту (не в группе) — заносим
    в ClickUp так же, как задачи из групповых чатов: с классификацией по проекту
    (Atlas/Алтын/BestSwift), а если по тексту не понятно, к какому проекту это относится —
    в "Unsorted" (личка не привязана к одному проекту, а спрашивать классификацию прямо в
    разговоре с Twin неуместно — это отдельная папка на разбор, как и для групп). Обычный
    разговорный обмен репликами task_extractor и так отфильтровывает (см.
    task_extractor._TASK_RULES — не каждое сообщение порождает задачу). Не должно мешать
    основному ответу Twin — любая ошибка тут только логируется, наружу не всплывает."""
    if not config.CLICKUP_ENABLED:
        return
    chat_title = "Личка Марины"
    reporter_display_name = user.first_name or "Марина"
    try:
        tasks = task_extractor.extract_tasks_classified(
            chat_title, [{"user_name": reporter_display_name, "text": text, "ts": time.time()}]
        )
    except Exception:
        logger.exception("Ошибка извлечения задач из личного сообщения владелицы")
        return
    if not tasks:
        return
    # Личка владелицы — репортер всегда она сама (единственный собеседник Twin в личке),
    # сопоставлять reporter_name из экстрактора не с чем гадать: сразу берём её же
    # telegram username (часть 33, "от кого задача").
    created = _push_tasks(
        user.id, chat_title, tasks, lambda t: t.get("project") or "unsorted",
        reporter_lookup={reporter_display_name: user.username},
    )
    if created:
        logger.info("Из личного сообщения владелицы занесено задач в ClickUp: %s", created)


_PRIORITY_LABELS = {"urgent": "🔴 Срочно", "high": "🟠 Высокий приоритет", "normal": "Обычный приоритет", "low": "Низкий приоритет"}


def _manual_task_confirm_keyboard(manual_task_id: int):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("❌ Отменить", callback_data=f"mtask_cancel:{manual_task_id}"),
                InlineKeyboardButton("✅ Создать", callback_data=f"mtask_confirm:{manual_task_id}"),
            ]
        ]
    )


def _render_manual_task_preview(
    target_label: str, title: str, description: str, status_name: str | None,
    priority: str, assignee_name: str,
) -> str:
    lines = [f"📋 Похоже, нужно поставить задачу в «{target_label}»:", "", f"«{title}»"]
    if description:
        lines.append(description)
    details = []
    if assignee_name:
        details.append(f"👤 {assignee_name}")
    if status_name:
        details.append(f"Статус: {status_name}")
    details.append(_PRIORITY_LABELS.get(priority, priority))
    lines.append(" · ".join(details))
    lines.append("")
    lines.append("Создать?")
    return "\n".join(lines)


async def _propose_explicit_task_command(context: ContextTypes.DEFAULT_TYPE, user, text: str) -> bool:
    """Если сообщение владелицы в личке — явная, осознанная команда поставить ОДНУ
    конкретную задачу в конкретный ClickUp-список (и, возможно, конкретный статус),
    например "Поставь Свете задачу в WEEKLY в статус Понедельник с пометкой срочно ..."
    (по прямой просьбе владелицы, 06.09) — извлекает данные (task_command.extract_task_command,
    лёгкая модель) и присылает превью с кнопками "❌ Отменить"/"✅ Создать". Задача реально
    создаётся в ClickUp только по нажатию "✅ Создать" (см. handle_manual_task_callback), не
    здесь. В отличие от обычного фонового логирования задач (_log_owner_dm_tasks), эта
    команда ЯВНО называет список/пространство — вызывающий код (handle_message) должен
    пропустить _log_owner_dm_tasks для этого же сообщения, если эта функция вернула True
    (иначе задача задвоится). Возвращает True, если сообщение было опознано и обработано
    этой командой (даже если список/статус не удалось сопоставить — в этом случае вместо
    черновика владелице прямо пишется, чего не хватило, с реальными вариантами), и False,
    если сообщение вообще не похоже на такую явную команду — тогда handle_message
    обрабатывает его как раньше (_log_owner_dm_tasks)."""
    if not config.CLICKUP_ENABLED or not config.CLICKUP_TASK_TARGETS:
        return False
    try:
        parsed = task_command.extract_task_command(text)
    except Exception:
        logger.exception("Ошибка при разборе явной команды на постановку задачи")
        return False
    if not parsed:
        return False

    resolved_target = _resolve_task_target(parsed["target_name"])
    if not resolved_target:
        known = ", ".join(t["label"] for t in config.CLICKUP_TASK_TARGETS.values())
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                f"Поняла, что нужно поставить задачу, но не разобрала, в какой именно список "
                f"(«{parsed['target_name']}») — знаю: {known}. Уточни, пожалуйста, название списка."
            ),
        )
        return True
    target_key, target = resolved_target
    list_id = target["list_id"]

    try:
        matched_status, available_statuses = _resolve_task_status(list_id, parsed["status_name"])
    except Exception:
        logger.exception("Не удалось получить статусы списка %s (задача «%s»)", list_id, parsed["title"])
        await context.bot.send_message(
            chat_id=user.id,
            text="Не смогла проверить статусы этого списка в ClickUp — попробуй ещё раз чуть позже.",
        )
        return True

    if parsed["status_name"] and not matched_status:
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                f"Не нашла статус «{parsed['status_name']}» в списке «{target['label']}». "
                f"Доступные статусы: {', '.join(available_statuses)}."
            ),
        )
        return True

    assignee_name = parsed["assignee_name"]
    assignee_id = _resolve_assignee_id(assignee_name) if assignee_name else None
    unresolved_assignee_note = ""
    if assignee_name and not assignee_id:
        unresolved_assignee_note = f"\n\n(не нашла «{assignee_name}» среди известных сотрудников — создам без ответственного)"

    manual_task_id = storage.add_pending_manual_task(
        user.id, text, target_key, list_id, parsed["title"], parsed["description"],
        matched_status, parsed["priority"], assignee_id, assignee_name or None,
    )
    preview = _render_manual_task_preview(
        target["label"], parsed["title"], parsed["description"], matched_status,
        parsed["priority"], assignee_name,
    ) + unresolved_assignee_note
    await context.bot.send_message(
        chat_id=user.id, text=preview, reply_markup=_manual_task_confirm_keyboard(manual_task_id)
    )
    return True


async def handle_manual_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает кнопки "❌ Отменить"/"✅ Создать" под превью явной команды на постановку
    задачи (см. _propose_explicit_task_command). Задача реально создаётся в ClickUp
    (clickup_client.create_task, с указанным статусом, если он был сопоставлен) только
    здесь, по "✅ Создать" — не в момент разбора текста."""
    query = update.callback_query
    await query.answer()

    if config.OWNER_USER_ID is not None and query.from_user.id != config.OWNER_USER_ID:
        return

    action, _, task_id_raw = (query.data or "").partition(":")
    try:
        manual_task_id = int(task_id_raw)
    except ValueError:
        return

    manual_task = storage.get_pending_manual_task(manual_task_id)
    if not manual_task or manual_task["resolved"]:
        await query.edit_message_text("Этот черновик задачи уже не актуален.")
        return

    if action == "mtask_cancel":
        storage.resolve_pending_manual_task(manual_task_id)
        await query.edit_message_text("Хорошо, не создаю.")
        return

    if action == "mtask_confirm":
        try:
            result = clickup_client.create_task(
                manual_task["list_id"],
                name=manual_task["title"],
                description=manual_task["description"] or "",
                priority=manual_task["priority"],
                assignees=[manual_task["assignee_id"]] if manual_task["assignee_id"] else None,
                status=manual_task["status_name"] or None,
            )
        except Exception:
            logger.exception("Не удалось создать задачу в ClickUp (черновик #%s)", manual_task_id)
            await query.edit_message_text(
                "Не смогла создать задачу в ClickUp (возможно, проблема с доступом) — "
                f"добавь, пожалуйста, вручную: «{manual_task['title']}»"
            )
            return
        task_id = str(result.get("id", ""))
        # Реальная задача из явной команды владелицы в личке — "от кого" тут всегда она
        # сама (часть 33, "от кого задача"), гадать/сопоставлять не нужно.
        reporter = query.from_user
        storage.log_pushed_task(
            manual_task["owner_user_id"], "Личка Марины", task_id, manual_task["title"], manual_task["target_key"],
            reporter_name=(reporter.first_name if reporter else None) or "Марина",
            reporter_username=reporter.username if reporter else None,
        )
        storage.resolve_pending_manual_task(manual_task_id)
        await query.edit_message_text(f"Готово, создала задачу: «{manual_task['title']}» ✅")


_WEEKDAYS_SHORT = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]


def _format_meeting_time(iso_str: str) -> str:
    """ISO 8601 → человекочитаемо для превью черновика встречи, например
    "08.09 (вт) 15:00". При ошибке разбора возвращает исходную строку как есть —
    лучше показать сырую дату, чем упасть на форматировании превью."""
    try:
        dt = datetime.fromisoformat(iso_str)
    except ValueError:
        return iso_str
    return dt.strftime(f"%d.%m ({_WEEKDAYS_SHORT[dt.weekday()]}) %H:%M")


def _meeting_confirm_keyboard(meeting_id: int):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✏️ Изменить", callback_data=f"cal_edit:{meeting_id}")],
            [
                InlineKeyboardButton("❌ Отменить", callback_data=f"cal_cancel:{meeting_id}"),
                InlineKeyboardButton("✅ Применить", callback_data=f"cal_confirm:{meeting_id}"),
            ],
        ]
    )


def _render_meeting_preview(
    title: str,
    start_iso: str,
    end_iso: str,
    location: str,
    *,
    editing: bool = False,
    overlap_warning: str = "",
) -> str:
    """Текст превью черновика встречи. overlap_warning (см. _build_overlap_warning) —
    необязательная строка-предупреждение о пересечении по времени; пустая строка ничего
    не добавляет."""
    start_human = _format_meeting_time(start_iso)
    end_human = _format_meeting_time(end_iso)
    location_line = f"\n📍 {location}" if location else ""
    warning_line = f"\n\n{overlap_warning}" if overlap_warning else ""
    heading = "📅 Обновила черновик встречи:" if editing else "📅 Похоже, ты хочешь поставить встречу:"
    return f"{heading}\n\n«{title}»\n{start_human} – {end_human}{location_line}{warning_line}\n\nПрименить?"


def _build_overlap_warning(start_iso: str, end_iso: str) -> str:
    """Проверяет через calendar_client.find_overlapping_events пересечение по времени —
    только предупреждает в превью, не блокирует постановку (решение за владелицей).
    Любая ошибка молча даёт пустое предупреждение."""
    if not config.GOOGLE_CALENDAR_ENABLED:
        return ""
    try:
        overlaps = calendar_client.find_overlapping_events(start_iso, end_iso)
    except Exception:
        logger.exception("Не удалось проверить пересечения по времени для новой встречи")
        return ""

    if not overlaps:
        return ""

    lines = [f"«{ev['title']}» ({_format_meeting_time(ev['start'])})" for ev in overlaps[:3]]
    return "⚠️ Пересекается по времени с: " + "; ".join(lines)


async def _propose_meeting_draft(context: ContextTypes.DEFAULT_TYPE, user, text: str) -> None:
    """Если сообщение владелицы в личке похоже на просьбу поставить встречу — извлекает
    название/время (meeting_extractor.extract_meeting, лёгкая модель без базы знаний) и
    присылает черновик с кнопками "✏️ Изменить"/"❌ Отменить"/"✅ Применить". Событие в
    Google Calendar реально создаётся только по нажатию "✅ Применить" (см.
    handle_calendar_callback) — calendar_client.create_event отсюда не вызывается. Молча
    ничего не делает, если Google Calendar не настроен (config.GOOGLE_CALENDAR_ENABLED)
    или сообщение не похоже на просьбу поставить встречу. Не мешает основному ответу
    Twin — вызывается параллельно, как и _log_owner_dm_tasks для задач; любая ошибка тут
    только логируется, наружу не всплывает."""
    if not config.GOOGLE_CALENDAR_ENABLED:
        return
    try:
        meeting = meeting_extractor.extract_meeting(text, config.MARINATWIN_TIMEZONE)
    except Exception:
        logger.exception("Ошибка при разборе сообщения на предмет встречи")
        return
    if not meeting:
        return

    meeting_id = storage.add_pending_meeting(
        user.id, text, meeting["title"], meeting["start"], meeting["end"], meeting["location"]
    )
    overlap_warning = _build_overlap_warning(meeting["start"], meeting["end"])
    preview = _render_meeting_preview(
        meeting["title"], meeting["start"], meeting["end"], meeting["location"], overlap_warning=overlap_warning
    )
    await context.bot.send_message(
        chat_id=user.id, text=preview, reply_markup=_meeting_confirm_keyboard(meeting_id)
    )


async def _apply_meeting_edit(context: ContextTypes.DEFAULT_TYPE, user, meeting: dict, text: str) -> None:
    """Владелица нажала "✏️ Изменить" под черновиком встречи (см. handle_calendar_callback,
    action "cal_edit") и следующим сообщением прислала исправленный текст — перехватывается
    в handle_message раньше обычной обработки личного сообщения (см. get_meeting_awaiting_edit).
    Заново прогоняет текст через meeting_extractor и обновляет ТОТ ЖЕ черновик (тот же
    meeting_id, не создаёт новый), затем снова показывает превью с теми же тремя
    кнопками. Если новый текст тоже не удалось разобрать — awaiting_edit не снимается
    (см. storage.get_meeting_awaiting_edit/update_meeting_details), можно сразу
    попробовать ещё раз, не нажимая "Изменить" заново."""
    meeting_id = meeting["id"]
    try:
        parsed = meeting_extractor.extract_meeting(text, config.MARINATWIN_TIMEZONE)
    except Exception:
        logger.exception("Ошибка при разборе исправленного текста встречи (#%s)", meeting_id)
        parsed = None
    if not parsed:
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                "Не поняла — опиши, пожалуйста, ещё раз с датой и временем "
                "(можно приблизительно, например «в четверг в 15:00»)."
            ),
        )
        return
    storage.update_meeting_details(meeting_id, parsed["title"], parsed["start"], parsed["end"], parsed["location"])
    overlap_warning = _build_overlap_warning(parsed["start"], parsed["end"])
    preview = _render_meeting_preview(
        parsed["title"], parsed["start"], parsed["end"], parsed["location"], editing=True, overlap_warning=overlap_warning
    )
    await context.bot.send_message(
        chat_id=user.id, text=preview, reply_markup=_meeting_confirm_keyboard(meeting_id)
    )


def _mirror_meeting_to_clickup(meeting: dict) -> None:
    """Дублирует подтверждённую встречу в ClickUp-список config.CLICKUP_LIST_SCHEDULE
    (папка "Расписание Марина Twin" → список "Встречи") — по просьбе владелицы, чтобы
    видеть своё расписание и там же, где остальные задачи. Приватность (видит только
    она) обеспечивается настройками самого списка в ClickUp (Guests & Permissions), не
    этим кодом. Если список не настроен — тихо ничего не делает. Любая ошибка только
    логируется: неудачное зеркалирование не должно откатывать уже созданное событие в
    Google Calendar и не должно ломать подтверждение для владелицы (см.
    handle_calendar_callback — событие в календаре уже создано к моменту этого вызова)."""
    if not config.CLICKUP_LIST_SCHEDULE:
        return
    try:
        start_dt = datetime.fromisoformat(meeting["start_iso"])
        end_dt = datetime.fromisoformat(meeting["end_iso"])
        start_ms = int(start_dt.timestamp() * 1000)
        due_ms = int(end_dt.timestamp() * 1000)
    except ValueError:
        start_ms = due_ms = None
    description = f"📍 {meeting['location']}" if meeting.get("location") else ""
    try:
        clickup_client.create_task(
            config.CLICKUP_LIST_SCHEDULE,
            name=meeting["title"],
            description=description,
            start_date_ms=start_ms,
            due_date_ms=due_ms,
        )
    except Exception:
        logger.exception("Не удалось продублировать встречу в ClickUp (расписание): %s", meeting["title"])


async def handle_calendar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает кнопки "✏️ Изменить"/"❌ Отменить"/"✅ Применить" под черновиком
    встречи (см. _propose_meeting_draft). Реальное создание события в Google Calendar
    (calendar_client.create_event) происходит только здесь, по "✅ Применить" — не в
    момент разбора текста. "✏️ Изменить" ничего не создаёт и не отменяет — только
    переводит черновик в режим ожидания исправленного текста (см.
    storage.set_meeting_awaiting_edit, обрабатывается дальше в handle_message →
    _apply_meeting_edit)."""
    query = update.callback_query
    await query.answer()

    if config.OWNER_USER_ID is not None and query.from_user.id != config.OWNER_USER_ID:
        return

    action, _, meeting_id_raw = (query.data or "").partition(":")
    try:
        meeting_id = int(meeting_id_raw)
    except ValueError:
        return

    meeting = storage.get_meeting(meeting_id)
    if not meeting or meeting["resolved"]:
        await query.edit_message_text("Этот черновик встречи уже не актуален.")
        return

    if action == "cal_cancel":
        storage.cancel_meeting(meeting_id)
        await query.edit_message_text("Хорошо, не добавляю в календарь.")
        return

    if action == "cal_edit":
        storage.set_meeting_awaiting_edit(meeting_id, True)
        await query.edit_message_text(
            f"✏️ Хорошо, напиши, как исправить «{meeting['title']}» — пришлю новый черновик."
        )
        return

    if action == "cal_confirm":
        try:
            event_id = calendar_client.create_event(
                meeting["title"],
                meeting["start_iso"],
                meeting["end_iso"],
                location=meeting["location"] or None,
            )
        except Exception:
            logger.exception("Не удалось создать событие в Google Calendar (встреча #%s)", meeting_id)
            await query.edit_message_text(
                "Не смогла добавить в календарь (возможно, проблема с доступом) — "
                "добавь, пожалуйста, вручную: "
                f"«{meeting['title']}», {_format_meeting_time(meeting['start_iso'])}"
            )
            return
        storage.resolve_meeting(meeting_id, event_id)
        _mirror_meeting_to_clickup(meeting)
        await query.edit_message_text(f"Готово, добавила в календарь: «{meeting['title']}» 📅")


_CALENDAR_PERIOD_LABELS = {
    "today": "Сегодня",
    "tomorrow": "Завтра",
    "this_week": "Текущая неделя",
    "next_week": "Следующая неделя",
    "this_month": "Текущий месяц",
}


def _calendar_period_bounds(period: str) -> tuple[datetime, datetime] | None:
    """Возвращает полуоткрытый интервал [начало, конец) для одной из пяти кнопок
    команды /calendar (см. handle_calendar_view_callback), в часовом поясе
    config.MARINATWIN_TIMEZONE — тот же пояс, что используется для постановки
    встреч (meeting_extractor), а не часовой пояс самого календаря (m@altyn.one
    настроен на Asia/Dubai) — чтобы "сегодня"/"эта неделя" совпадали с тем, как
    Марина сама мыслит о времени. Неделя считается с понедельника (российское
    бытовое соглашение), месяц — с 1 числа по 1 число следующего месяца. Возвращает
    None для неизвестного ключа периода (не должно происходить при обычном
    использовании кнопок, но защищает от неожиданного callback_data)."""
    tz = ZoneInfo(config.MARINATWIN_TIMEZONE)
    today_start = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "today":
        return today_start, today_start + timedelta(days=1)
    if period == "tomorrow":
        start = today_start + timedelta(days=1)
        return start, start + timedelta(days=1)
    if period == "this_week":
        monday = today_start - timedelta(days=today_start.weekday())
        return monday, monday + timedelta(days=7)
    if period == "next_week":
        monday = today_start - timedelta(days=today_start.weekday()) + timedelta(days=7)
        return monday, monday + timedelta(days=7)
    if period == "this_month":
        start = today_start.replace(day=1)
        end = start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(month=start.month + 1)
        return start, end
    return None


def _calendar_period_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Сегодня", callback_data="calview:today"),
                InlineKeyboardButton("Завтра", callback_data="calview:tomorrow"),
            ],
            [
                InlineKeyboardButton("Текущая неделя", callback_data="calview:this_week"),
                InlineKeyboardButton("Следующая неделя", callback_data="calview:next_week"),
            ],
            [InlineKeyboardButton("Текущий месяц", callback_data="calview:this_month")],
        ]
    )


def _format_calendar_event_line(event: dict, tz: ZoneInfo) -> str:
    """Одна строка списка /calendar: "DD.MM (пн) HH:MM–HH:MM — Название 📍место".
    Для событий на весь день (event["all_day"]) время не показываем. При ошибке
    разбора даты показывает исходную строку как есть — лучше сырое значение, чем
    падение на форматировании целого списка из-за одного кривого события."""
    if event["all_day"]:
        try:
            d = datetime.fromisoformat(event["start"])
            time_part = f"{d.strftime('%d.%m')} ({_WEEKDAYS_SHORT[d.weekday()]}), весь день"
        except ValueError:
            time_part = event["start"]
    else:
        try:
            start_dt = datetime.fromisoformat(event["start"]).astimezone(tz)
            end_dt = datetime.fromisoformat(event["end"]).astimezone(tz)
            time_part = (
                f"{start_dt.strftime('%d.%m')} ({_WEEKDAYS_SHORT[start_dt.weekday()]}) "
                f"{start_dt.strftime('%H:%M')}–{end_dt.strftime('%H:%M')}"
            )
        except ValueError:
            time_part = f"{event['start']} – {event['end']}"
    location_part = f" 📍{event['location']}" if event.get("location") else ""
    return f"{time_part} — {event['title']}{location_part}"


async def handle_calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/calendar — только в личке, только для владелицы: предлагает выбрать период
    кнопками (Сегодня/Завтра/Текущая неделя/Следующая неделя/Текущий месяц), см.
    handle_calendar_view_callback — там и происходит реальный запрос к Google Calendar
    по нажатию кнопки."""
    chat = update.effective_chat
    if chat.type != "private":
        await update.message.reply_text("Эта команда работает только в личке.")
        return
    if config.OWNER_USER_ID is None or update.effective_user.id != config.OWNER_USER_ID:
        await update.message.reply_text("Эта команда только для владелицы.")
        return
    if not config.GOOGLE_CALENDAR_ENABLED:
        await update.message.reply_text("Google Calendar пока не настроен.")
        return
    await update.message.reply_text("Какой период показать?", reply_markup=_calendar_period_keyboard())


async def handle_calendar_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает кнопки периода под /calendar (см. handle_calendar_command и
    _calendar_period_keyboard) — тянет события ЖИВЬЁМ из Google Calendar API
    (calendar_client.list_events, весь календарь config.GOOGLE_CALENDAR_ID за период,
    не только встречи, поставленные самим ботом) и заменяет текст того же сообщения
    списком, оставляя те же кнопки — можно переключать период дальше, не вызывая
    /calendar заново. Список обрезается под лимит сообщения Telegram, если событий
    очень много (см. TELEGRAM_MESSAGE_LIMIT) — это команда просмотра одним
    сообщением, а не постраничный отчёт."""
    query = update.callback_query
    await query.answer()

    if config.OWNER_USER_ID is not None and query.from_user.id != config.OWNER_USER_ID:
        return

    _, _, period = (query.data or "").partition(":")
    bounds = _calendar_period_bounds(period)
    if not bounds:
        return
    start, end = bounds
    label = _CALENDAR_PERIOD_LABELS.get(period, period)

    try:
        events = calendar_client.list_events(start.isoformat(), end.isoformat())
    except Exception:
        logger.exception("Не удалось получить события календаря за период %s", period)
        await query.edit_message_text(
            f"Не смогла получить события календаря ({label}) — попробуй ещё раз чуть позже.",
            reply_markup=_calendar_period_keyboard(),
        )
        return

    tz = ZoneInfo(config.MARINATWIN_TIMEZONE)
    if not events:
        text = f"📅 {label}: событий нет."
    else:
        lines = [_format_calendar_event_line(e, tz) for e in events]
        header = f"📅 {label} ({len(events)}):\n\n"
        body = "\n".join(lines)
        if len(header) + len(body) > TELEGRAM_MESSAGE_LIMIT:
            # Слишком много событий для одного сообщения-превью — показываем сколько
            # влезает и честно говорим, что список неполный, а не режем список молча
            # или падаем на превышении лимита Telegram.
            budget = TELEGRAM_MESSAGE_LIMIT - len(header) - 80
            truncated = body[:budget]
            cut = truncated.rfind("\n")
            if cut != -1:
                truncated = truncated[:cut]
            shown = truncated.count("\n") + 1 if truncated else 0
            body = f"{truncated}\n\n…и ещё {len(events) - shown} событий, не поместились — сузь период."
        text = header + body

    await query.edit_message_text(text, reply_markup=_calendar_period_keyboard())


"""Один и тот же чат может попасть на выгрузку из двух разных мест почти одновременно:
сразу после нового сообщения (см. handle_group_message) и по расписанию
(periodic_flush_job, независимый job на том же event loop). Раньше это иногда
приводило к тому, что оба вызова читали ОДИН и тот же непрочитанный буфер (ещё до
того, как первый успевал пометить его прочитанным — вызов Claude занимает заметное
время), и задача извлекалась дважды с чуть разными формулировками — на практике
наблюдалось как два похожих ClickUp-таска с разницей в несколько секунд и
дословно совпадающей цитатой источника. Лок на чат сериализует выгрузки одного и
того же чата: второй вызов дожидается первого и застаёт буфер уже пустым."""
_chat_flush_locks: dict[int, asyncio.Lock] = {}

def _get_chat_flush_lock(chat_id: int) -> asyncio.Lock:
    """Возвращает asyncio.Lock для указанного chat_id, создавая при необходимости."""
    lock = _chat_flush_locks.get(chat_id)
    if lock is None:
        lock = asyncio.Lock()
        _chat_flush_locks[chat_id] = lock
    return lock


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
    классифицируется отдельно (Atlas/Алтын/BestSwift), а то, что не удалось однозначно
    классифицировать, сразу уходит в "Разобрать" — БЕЗ уточняющего вопроса в чате (по
    прямой просьбе владелицы, часть 33: бот больше не переспрашивает в группах, только
    молча читает переписку и, если что, кладёт задачу в "Разобрать"; раньше здесь был
    отдельный поток с уточняющим вопросом в чате — см. историю/project status doc, части
    до 33). Сериализовано локом на chat_id (см. _get_chat_flush_lock) — защита от гонки
    между немедленной выгрузкой из handle_group_message и периодической
    (periodic_flush_job)."""
    async with _get_chat_flush_lock(chat_id):
        rows = storage.get_unflushed(chat_id)
        if not rows:
            return 0
        # "От кого задача" (часть 33) — сопоставление reporter_name (см. task_extractor.py)
        # с реальным Telegram @username строится ИЗ ЭТОГО ЖЕ буфера сообщений, пока он ещё
        # не стёр (mark_flushed ниже) — иначе к моменту, когда неоднозначная задача
        # разрешится (ответ в чате или таймаут), исходные сообщения уже не найти.
        reporter_lookup = _reporter_lookup_from_rows(rows)
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
            created = _push_tasks(chat_id, chat_title, tasks, lambda _t: project_key, reporter_lookup)
        else:
            try:
                tasks = task_extractor.extract_tasks_classified(chat_title, rows)
            except Exception:
                logger.exception(
                    "Ошибка извлечения/классификации задач для чата %s (%s) — оставляю буфер непрочитанным, попробую ещё раз",
                    chat_id, chat_title,
                )
                return 0
            # Раньше задачи, которые не удалось однозначно классифицировать, сначала
            # переспрашивались в чате (see _ask_classification_question — убрано в части
            # 33) — теперь всё, что не Atlas/Алтын/BestSwift, просто идёт в "Разобрать",
            # без вопроса в группу.
            created = _push_tasks(
                chat_id, chat_title, tasks,
                lambda t: t.get("project") if t.get("project") in ("atlas", "altyn", "bestswift") else "unsorted",
                reporter_lookup,
            )
        storage.mark_flushed(chat_id)
        return created


_URGENT_PRIORITIES = {"urgent", "high"}


def _is_urgent(task: dict) -> bool:
    return (task.get("priority") or "") in _URGENT_PRIORITIES


def _is_fire(task: dict) -> bool:
    """Задача помечена "🔥 Горит», если среди её тегов ClickUp есть
    config.CLICKUP_FIRE_TAG_NAME (по прямой просьбе владелицы, часть 27 — с этой части
    это настоящий тег ClickUp, а не локальная пометка внутри бота, как раньше в части 24,
    см. clickup_client.ensure_tag_on_task). Сравнение без учёта регистра — на случай, если
    тег в ClickUp когда-то создан/переименован с другим регистром букв."""
    fire_name = config.CLICKUP_FIRE_TAG_NAME.lower()
    return any((tg or "").lower() == fire_name for tg in task.get("tags") or [])


def _format_task_location(task: dict) -> str:
    """Строит короткую строку "где стоит задача" — пространство / папка / список ClickUp
    (по прямой просьбе владелицы, часть 27: команды по сотрудникам ищут задачи по всему
    workspace, и не всегда очевидно, из какого именно места они пришли). Использует только
    то, что реально известно (см. clickup_client.get_open_tasks_team_wide) — пропускает
    отсутствующие части, а не подставляет заглушки. Пространство разрешается по
    config.CLICKUP_SPACE_NAMES (сам ClickUp API не отдаёт имя пространства в объекте
    задачи, только id) — если id незнаком (новое пространство завели после последнего
    обновления этого словаря), просто пропускается, а не показывается как "?"."""
    parts = []
    space_id = task.get("space_id")
    if space_id:
        space_name = config.CLICKUP_SPACE_NAMES.get(str(space_id))
        if space_name:
            parts.append(space_name)
    folder_name = task.get("folder_name")
    if folder_name:
        parts.append(folder_name)
    list_name = task.get("list_name")
    if list_name:
        parts.append(list_name)
    return " / ".join(parts)


def _format_due_suffix(due_date: float | None) -> str:
    """Возвращает суффикс со сроком «(до ДД.ММ.ГГГГ)» для строки отчёта, если у задачи
    задан срок в ClickUp, иначе пустую строку."""
    if not due_date:
        return ""
    dt = datetime.fromtimestamp(due_date, tz=ZoneInfo(config.MARINATWIN_TIMEZONE))
    return f" (до {dt.strftime('%d.%m.%Y')})"


def _format_attribution_suffix(task: dict, reporters: dict[str, dict]) -> str:
    """По прямой просьбе владелицы, часть 33 ("от кого задача и к кому обращается —
    ник в тг и на кого задача"): строит суффикс вида " [от @ivan_tg → Дима]" для строки
    отчёта. "→ Дима" — реальные ответственные ClickUp прямо из задачи (см.
    clickup_client._extract_assignee_names, поле "assignees" — живые, актуальные на
    момент запроса, а не то, что было на момент постановки). "от ..." — кто в переписке
    поднял задачу (см. storage.get_task_reporters — известно только для задач, которые
    завёл сам бот; для задач, заведённых вручную прямо в ClickUp, неизвестно и просто
    опускается, как и остальные "если известно" в этом боте). Если неизвестно ни то,
    ни другое — возвращает пустую строку, ничего лишнего в строке не появляется."""
    reporter = reporters.get(task.get("id")) or {}
    reporter_name = (reporter.get("reporter_name") or "").strip()
    reporter_username = (reporter.get("reporter_username") or "").strip()
    assignees = task.get("assignees") or []
    parts = []
    if reporter_name and reporter_username:
        parts.append(f"от {reporter_name} (@{reporter_username})")
    elif reporter_username:
        parts.append(f"от @{reporter_username}")
    elif reporter_name:
        parts.append(f"от {reporter_name}")
    if assignees:
        parts.append(f"→ {', '.join(assignees)}")
    return f" [{' · '.join(parts)}]" if parts else ""


def _format_task_lines(tasks: list[dict]) -> list[str]:
    """Форматирует список задач ClickUp (см. clickup_client.get_open_tasks) в пронумерованные
    строки отчёта, отмечая срочные/высокоприоритетные задачи значком 🔴, дописывая срок (если
    задан в ClickUp) и, если известно, "от кого/на кого" (см. _format_attribution_suffix,
    часть 33) в конце строки."""
    reporters = storage.get_task_reporters([t["id"] for t in tasks if t.get("id")])
    lines = []
    for i, t in enumerate(tasks, start=1):
        marker = "🔴 " if _is_urgent(t) else ""
        due_suffix = _format_due_suffix(t.get("due_date"))
        attribution_suffix = _format_attribution_suffix(t, reporters)
        lines.append(f"{i}. {marker}{t['name']}{due_suffix}{attribution_suffix}")
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


async def handle_cancelall_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/cancelall — только в личке, только владелице: она сама, вживую, уже ответила
    на висящие вопросы прямо в группах (или решила, что бот отвечать не должен) — и не
    хочет, чтобы бот всё ещё ждал её ответа в личке или напоминал об этих вопросах.
    Разом снимает ВСЕ ещё не закрытые через бота эскалации (см.
    storage.cancel_all_pending_escalations) — бот в эти чаты по этим вопросам больше не
    вернётся и черновики/кнопки по ним больше не актуальны."""
    chat = update.effective_chat
    if chat.type != "private":
        await update.message.reply_text("Эта команда работает только в личке.")
        return
    if config.OWNER_USER_ID is None or update.effective_user.id != config.OWNER_USER_ID:
        await update.message.reply_text("Эта команда только для владелицы.")
        return
    cancelled = storage.cancel_all_pending_escalations()
    if cancelled:
        await update.message.reply_text(
            f"Поняла, сняла все висящие вопросы ({cancelled} шт.) — раз ты уже ответила "
            f"сама, в эти чаты возвращаться не буду."
        )
    else:
        await update.message.reply_text("Висящих вопросов и не было — всё чисто.")


async def handle_stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/stop — только в личке, только владелице (по прямой просьбе владелицы, часть 33):
    "если я вдруг ошибочно нажала команду 'Править' и начались выгружаться по одной
    задачи в телегу" — прерывает рассылку режима правки (см. _send_edit_mode_report/
    _request_stop_edit_mode) перед следующим же сообщением. Ничего не ломает, если
    рассылка на самом деле не идёт — просто выставляет флаг, который никто не проверит,
    пока не запустится следующая; отвечает одинаково в обоих случаях, чтобы не пытаться
    гадать, идёт рассылка прямо сейчас или уже нет (гонка между проверкой и ответом всё
    равно возможна)."""
    chat = update.effective_chat
    if chat.type != "private":
        await update.message.reply_text("Эта команда работает только в личке.")
        return
    if config.OWNER_USER_ID is None or update.effective_user.id != config.OWNER_USER_ID:
        await update.message.reply_text("Эта команда только для владелицы.")
        return
    _request_stop_edit_mode()
    await update.message.reply_text("🛑 Хорошо, останавливаю рассылку задач (если она сейчас идёт).")


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


# Небольшая пауза между сообщениями режима правки (по прямой просьбе владелицы, часть 28:
# на каждую задачу отдельное Telegram-сообщение со своими кнопками — см.
# _send_edit_mode_report) — при большом числе задач (например, у Лили их около 80)
# рассылка десятков сообщений подряд без паузы рискует упереться в лимит Telegram на
# сообщения в один чат (см. также RetryAfter-обработку в _send_owner_message_with_retry).
_TASK_MESSAGE_DELAY_SECONDS = 0.35


# Флаг "остановить рассылку режима правки" (команда /stop, по прямой просьбе владелицы,
# часть 33: "если я вдруг ошибочно нажала команду 'Править' и начались выгружаться по
# одной задачи в телегу"). Простой модульный флаг, а не что-то в storage (БД) — рассылка
# живёт только в пределах одного вызова _send_edit_mode_report, персистентность между
# перезапусками бота не нужна, а владелица (единственная, кому доступны эти команды) может
# запустить только одну рассылку за раз. Сбрасывается в False в НАЧАЛЕ каждого нового
# вызова _send_edit_mode_report — иначе случайно нажатый /stop заблокировал бы все
# последующие "Править" впредь.
_stop_edit_mode_requested = False


def _request_stop_edit_mode() -> None:
    global _stop_edit_mode_requested
    _stop_edit_mode_requested = True


def _sort_tasks_fire_first(tasks: list[dict]) -> list[dict]:
    """Задачи, помеченные тегом ClickUp "кричащая задача" (кнопка "🔥 Горит», см.
    _is_fire/handle_employee_task_callback), идут первыми (в своём относительном порядке
    между собой), остальные — как были получены от ClickUp."""
    fire = [t for t in tasks if _is_fire(t)]
    rest = [t for t in tasks if not _is_fire(t)]
    return fire + rest


def _format_employee_task_lines(tasks: list[dict], start_index: int = 1) -> list[str]:
    """Как _format_task_lines, но для отчёта по сотруднику (см. _send_employee_report) —
    задачи теперь могут быть из любого места ClickUp (см.
    clickup_client.get_open_tasks_team_wide), поэтому в конце строки, если известно,
    дописывается местоположение задачи (пространство / папка / список — см.
    _format_task_location; по прямой просьбе владелицы, часть 27). start_index — чтобы
    сквозная нумерация не сбивалась, если этот список задач — часть большего отчёта.
    Используется и для компактного списка по умолчанию (см. _send_compact_report, часть
    29, без кнопок под строками), и для режима правки (см. _send_edit_mode_report, часть
    28-29 — там каждая строка уходит отдельным Telegram-сообщением сразу со своими
    кнопками под ней, см. _employee_task_keyboard).
    Задачи, помеченные "🔥 Горит" (см. _is_fire), получают значок 🔥 вместо обычного 🔴 у
    срочных — визуально понятно, что задача поднята вручную, а не просто высокий
    приоритет в ClickUp. Если известно (часть 33, "от кого задача и на кого") — в конце
    строки, после местоположения, добавляется ещё один суффикс "[от .../→ ...]" (см.
    _format_attribution_suffix)."""
    reporters = storage.get_task_reporters([t["id"] for t in tasks if t.get("id")])
    lines = []
    for offset, t in enumerate(tasks):
        i = start_index + offset
        marker = "🔥 " if _is_fire(t) else ("🔴 " if _is_urgent(t) else "")
        due_suffix = _format_due_suffix(t.get("due_date"))
        location = _format_task_location(t)
        location_suffix = f" [{location}]" if location else ""
        attribution_suffix = _format_attribution_suffix(t, reporters)
        lines.append(f"{i}. {marker}{t['name']}{due_suffix}{location_suffix}{attribution_suffix}")
    return lines


def _employee_task_keyboard(task: dict, include_weekly_button: bool = False) -> InlineKeyboardMarkup:
    """Строит кнопки-действия под ОДНОЙ задачей в режиме правки (по прямой просьбе
    владелицы, 06.09-часть 24, кнопка "📆 Weekly" — часть 27, "➡️ Переслать" — часть 29,
    см. handle_employee_task_callback). Первый ряд: "✅ Готово" (закрывает задачу в
    ClickUp), "🗑 Удалить" (удаляет из ClickUp насовсем, с шагом подтверждения),
    "➡️ Переслать" (пересылает эту задачу конкретному сотруднику в Telegram, см.
    _available_forward_recipients — рядом с "Удалить" по прямой просьбе владелицы).
    Второй ряд: "🔴 Срочно" (ставит приоритет Urgent в ClickUp), "🔥 Горит" (ставит/снимает
    настоящий тег ClickUp "кричащая задача", см. _is_fire — поднимает задачу наверх списка
    при следующем вызове команды), и, если include_weekly_button — "📆 Weekly" (переносит
    задачу в список WEEKLY TASKS со статусом Unsorted; только там, где задачи и так ищутся
    по всему ClickUp — переносить в weekly-отчётах, которые и так уже из WEEKLY TASKS,
    бессмысленно). Разбито на 2 ряда, а не 1 (как в части 28), чтобы 6 подписанных
    текстом кнопок не становились слишком узкими/тесными на экране телефона.
    Показывается только в режиме правки (см. _send_edit_mode_report, попадаем туда через
    кнопку "✏️ Править" под компактным списком, часть 29) — компактный список сам по себе
    кнопок под задачами не несёт."""
    task_id = task["id"]
    row1 = [
        InlineKeyboardButton("✅ Готово", callback_data=f"emp:done:{task_id}"),
        InlineKeyboardButton("🗑 Удалить", callback_data=f"emp:delask:{task_id}"),
        InlineKeyboardButton("➡️ Переслать", callback_data=f"emp:fwdask:{task_id}"),
    ]
    row2 = [
        InlineKeyboardButton("🔴 Срочно", callback_data=f"emp:urgent:{task_id}"),
        InlineKeyboardButton("🔥 Горит", callback_data=f"emp:fire:{task_id}"),
    ]
    if include_weekly_button:
        row2.append(InlineKeyboardButton("📆 Weekly", callback_data=f"emp:weekly:{task_id}"))
    return InlineKeyboardMarkup([row1, row2])


def _resolve_employee_telegram_id(employee_key: str) -> int | None:
    """Настоящий telegram_user_id сотрудника, если он уже известен — сначала смотрим
    ручную настройку (env-переменная TELEGRAM_ID_*, см.
    config._EMPLOYEE_TELEGRAM_ID_ENV — считается более авторитетной, раз задана явно
    владелицей), иначе — автоматически распознанный по @username (часть 30, см.
    _maybe_capture_employee_telegram_id/storage.get_employee_telegram_id). None — если
    ни то, ни другое неизвестно."""
    employee = config.EMPLOYEE_COMMANDS.get(employee_key)
    manual_id = employee.get("telegram_user_id") if employee else None
    if manual_id:
        return manual_id
    return storage.get_employee_telegram_id(employee_key)


def _available_forward_recipients() -> list[tuple[str, str]]:
    """Возвращает [(employee_key, label), ...] только для тех сотрудников, у кого уже
    известен telegram_user_id — вручную (config._EMPLOYEE_TELEGRAM_ID_ENV) или
    автоматически по @username (часть 30, см. _resolve_employee_telegram_id) — по прямой
    просьбе владелицы: пересылка технически возможна только тем, чей Telegram user_id
    уже известен (человек должен был хоть раз сам написать боту), поэтому список
    получателей строится из уже настроенных, а не из всех config.EMPLOYEE_COMMANDS."""
    return [
        (key, employee["label"])
        for key, employee in config.EMPLOYEE_COMMANDS.items()
        if _resolve_employee_telegram_id(key)
    ]


def _no_forward_recipients_text() -> str:
    """Единый текст на случай, если владелица ещё не прислала ни одного telegram
    id/@username сотрудников (см. _available_forward_recipients) — и кнопка "Переслать"
    (что на компактном списке, что под отдельной задачей) не падает, а прямо объясняет,
    чего не хватает."""
    return (
        "Пока не знаю ничьих Telegram id — пришли мне @username или numeric id нужных "
        "сотрудников (например, попроси их написать что-нибудь боту @userinfobot, он в "
        "ответ покажет их id), и я включу пересылку."
    )


async def _send_owner_message_with_retry(
    context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup: InlineKeyboardMarkup | None = None
) -> None:
    """Шлёт одно сообщение владелице в личку с одной попыткой повтора при HTTP 429 от
    Telegram (RetryAfter) — по прямой просьбе владелицы, часть 28: с переходом на "одно
    сообщение на задачу" в режиме правки (см. _send_edit_mode_report) сообщений в один чат
    подряд стало ощутимо больше (например, у Лили ~80 задач), и Telegram иногда просит
    подождать между сообщениями в один и тот же чат. Любая другая ошибка отправки просто
    поднимается дальше — вызывающий код сам решает, как её залогировать/остановить
    рассылку."""
    try:
        await context.bot.send_message(chat_id=config.OWNER_USER_ID, text=text, reply_markup=reply_markup)
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after + 0.1)
        await context.bot.send_message(chat_id=config.OWNER_USER_ID, text=text, reply_markup=reply_markup)


_EDIT_MODE_BATCH_SIZE = 10


def _report_action_keyboard(kind: str, key: str) -> InlineKeyboardMarkup:
    """Кнопки под компактным списком задач (по прямой просьбе владелицы, часть 29):
    "✏️ Править" — открывает режим правки для этого же набора задач (см.
    handle_report_action_callback/_send_edit_mode_report), "➡️ Переслать" — пересылает
    ВЕСЬ этот список конкретному сотруднику в Telegram (см.
    _available_forward_recipients/_forward_report_to_employee). kind/key кодируют, какой
    именно отчёт заново запросить при нажатии (см. _fetch_report_data) — "emp"/employee_key
    (по всему ClickUp), "empw"/employee_key (только WEEKLY TASKS этого человека),
    "ws"/command_key (WEEKLY TASKS по статусу) — короткие, чтобы не упереться в лимит
    Telegram на длину callback_data (64 байта)."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✏️ Править", callback_data=f"rpt:edit:{kind}:{key}"),
                InlineKeyboardButton("➡️ Переслать", callback_data=f"rpt:fwd:{kind}:{key}"),
            ]
        ]
    )


async def _send_compact_report(
    context: ContextTypes.DEFAULT_TYPE,
    kind: str,
    key: str,
    label: str,
    scope_note: str,
    tasks: list[dict],
    include_weekly_button: bool = False,
) -> None:
    """Новый вид отчёта по умолчанию (по прямой просьбе владелицы, часть 29, заменяет
    прежний "по сообщению на задачу с кнопками" из части 28 — теперь ТАК выглядит только
    режим правки, см. _send_edit_mode_report): просто пронумерованный список задач с
    пометками 🔴/🔥 (см. _format_employee_task_lines), БЕЗ кнопок под каждой строкой, а под
    ВСЕМ списком — 2 кнопки, "✏️ Править" и "➡️ Переслать" (см. _report_action_keyboard).
    Список может не поместиться в одно Telegram-сообщение (лимит 4096 символов) — тогда
    режется на несколько (см. _split_for_telegram), а кнопки навешиваются только на
    последнее сообщение (Telegram не даёт кнопки нескольким сообщениям сразу).
    include_weekly_button передаётся дальше, в _send_edit_mode_report, если нажмут
    "Править" — сам компактный список кнопок под задачами не показывает."""
    if not tasks:
        try:
            await context.bot.send_message(
                chat_id=config.OWNER_USER_ID, text=f"👤 {label} — открытых задач {scope_note} не нашла.",
            )
        except Exception:
            logger.exception("Не удалось отправить отчёт по сотруднику (%s) владелице", label)
        return

    tasks = _sort_tasks_fire_first(tasks)
    total = len(tasks)
    header = f"👤 {label} — {scope_note} ({total}):"
    text = header + "\n" + "\n".join(_format_employee_task_lines(tasks, start_index=1))
    chunks = _split_for_telegram(text)
    keyboard = _report_action_keyboard(kind, key)
    try:
        for i, chunk in enumerate(chunks):
            await context.bot.send_message(
                chat_id=config.OWNER_USER_ID,
                text=chunk,
                reply_markup=keyboard if i == len(chunks) - 1 else None,
            )
    except Exception:
        logger.exception("Не удалось отправить отчёт по сотруднику (%s) владелице", label)


async def _send_edit_mode_report(
    context: ContextTypes.DEFAULT_TYPE,
    label: str,
    scope_note: str,
    tasks: list[dict],
    include_weekly_button: bool = False,
) -> None:
    """Режим правки (кнопка "✏️ Править" под компактным списком, см.
    _send_compact_report/handle_report_action_callback) — по прямой просьбе владелицы,
    часть 29: список разбивается на партии по _EDIT_MODE_BATCH_SIZE (10) задач, перед
    каждой партией — заголовок ("часть N/M"), и КАЖДАЯ задача внутри партии уходит
    отдельным Telegram-сообщением сразу со своими кнопками-действиями под ней (см.
    _employee_task_keyboard/handle_employee_task_callback) — так у каждой задачи буквально
    свои кнопки прямо под её текстом (было заведено в части 28, здесь только переехало из
    отчёта по умолчанию в отдельный режим правки). Задачи, помеченные "🔥 Горит",
    показываются первыми (см. _sort_tasks_fire_first). Между сообщениями — небольшая пауза
    (_TASK_MESSAGE_DELAY_SECONDS) во избежание лимита Telegram на сообщения в один чат
    (см. _send_owner_message_with_retry). По прямой просьбе владелицы, часть 33: команда
    /stop (см. handle_stop_command/_request_stop_edit_mode) прерывает рассылку между
    сообщениями (проверяется перед каждым заголовком партии и перед каждой задачей) — на
    случай, если "Править" нажали по ошибке, а задач много (например, у Лили их около 80,
    ждать, пока разошлются все, не всегда уместно)."""
    global _stop_edit_mode_requested
    _stop_edit_mode_requested = False
    if not tasks:
        try:
            await context.bot.send_message(
                chat_id=config.OWNER_USER_ID, text=f"👤 {label} — открытых задач {scope_note} не нашла.",
            )
        except Exception:
            logger.exception("Не удалось отправить отчёт по сотруднику (%s) владелице", label)
        return

    tasks = _sort_tasks_fire_first(tasks)
    total = len(tasks)
    lines = _format_employee_task_lines(tasks, start_index=1)
    batches = [
        list(zip(tasks[i : i + _EDIT_MODE_BATCH_SIZE], lines[i : i + _EDIT_MODE_BATCH_SIZE]))
        for i in range(0, total, _EDIT_MODE_BATCH_SIZE)
    ]
    sent_count = 0
    stopped = False
    try:
        for batch_num, batch in enumerate(batches, start=1):
            if _stop_edit_mode_requested:
                stopped = True
                break
            header = f"✏️ Правка: {label} — {scope_note} ({total})"
            if len(batches) > 1:
                header += f", часть {batch_num}/{len(batches)}"
            await _send_owner_message_with_retry(context, header)
            await asyncio.sleep(_TASK_MESSAGE_DELAY_SECONDS)
            for offset, (task, line) in enumerate(batch):
                if _stop_edit_mode_requested:
                    stopped = True
                    break
                keyboard = _employee_task_keyboard(task, include_weekly_button)
                await _send_owner_message_with_retry(context, line, reply_markup=keyboard)
                sent_count += 1
                is_last_message = batch_num == len(batches) and offset == len(batch) - 1
                if not is_last_message:
                    await asyncio.sleep(_TASK_MESSAGE_DELAY_SECONDS)
            if stopped:
                break
        if stopped:
            await _send_owner_message_with_retry(
                context, f"🛑 Остановлено по /stop — отправила {sent_count} из {total}."
            )
    except Exception:
        logger.exception("Не удалось отправить отчёт по сотруднику (%s) владелице", label)


async def _forward_report_to_employee(
    context: ContextTypes.DEFAULT_TYPE, label: str, scope_note: str, tasks: list[dict], recipient_key: str
) -> None:
    """Пересылает ВЕСЬ список задач (тот же формат, что и компактный отчёт, см.
    _format_employee_task_lines) конкретному сотруднику в Telegram — по прямой просьбе
    владелицы, часть 29 (кнопка "➡️ Переслать" под компактным списком, см.
    handle_report_action_callback). recipient_key — ключ config.EMPLOYEE_COMMANDS, у
    которого уже проверено (см. _available_forward_recipients), что известен
    telegram_user_id (см. _resolve_employee_telegram_id)."""
    recipient = config.EMPLOYEE_COMMANDS.get(recipient_key)
    recipient_chat_id = _resolve_employee_telegram_id(recipient_key) if recipient else None
    if not recipient or not recipient_chat_id:
        await context.bot.send_message(
            chat_id=config.OWNER_USER_ID, text="У этого человека пока не настроен Telegram id."
        )
        return
    if not tasks:
        await context.bot.send_message(
            chat_id=config.OWNER_USER_ID, text=f"«{label}» — открытых задач {scope_note} нет, пересылать нечего."
        )
        return
    tasks = _sort_tasks_fire_first(tasks)
    header = f"📤 Марина переслала: {label} — {scope_note} ({len(tasks)}):"
    text = header + "\n" + "\n".join(_format_employee_task_lines(tasks, start_index=1))
    try:
        for chunk in _split_for_telegram(text):
            await context.bot.send_message(chat_id=recipient_chat_id, text=chunk)
    except Exception:
        logger.exception("Не удалось переслать отчёт «%s» пользователю %s", label, recipient_key)
        await context.bot.send_message(
            chat_id=config.OWNER_USER_ID,
            text=f"Не смогла переслать «{label}» — проверь, писал ли этот человек боту раньше.",
        )
        return
    await context.bot.send_message(
        chat_id=config.OWNER_USER_ID, text=f"✅ Переслала «{label}» — {recipient['label']}."
    )


async def _send_employee_report(context: ContextTypes.DEFAULT_TYPE, employee_key: str) -> None:
    """/lili /olga /sveta /ilya /nazgul /alex /ub /marina /nikolay /nick — тянет живые
    открытые задачи этого конкретного человека ПО ВСЕМУ ClickUp (все пространства/папки/
    списки, см. clickup_client.get_open_tasks_team_wide), а не только из 4 официальных
    проектных списков (config.CLICKUP_LIST_IDS) — по прямой просьбе владелицы (06.09):
    сотрудники нередко ведут задачи и в личных папках/пространствах вне этих 4 проектов
    (например "Саша"/"Ник" в иерархии воркспейса). У большинства команд есть реальный
    ClickUp-аккаунт (assignee_id, config.EMPLOYEE_COMMANDS) — фильтрация идёт на стороне
    ClickUp API. У Саши (/alex) реального аккаунта нет — вместо этого задачи находятся по
    буквальному текстовому префиксу "Саша:" в начале названия (так их заводит
    task_extractor.py, когда не может сопоставить имя с реальным ClickUp-аккаунтом) — в
    этом случае приходится тянуть ВСЕ открытые задачи workspace без серверного фильтра и
    отфильтровывать по префиксу уже на своей стороне.

    С 06.09 (часть 24) каждая задача сопровождается кнопками-действиями, но только в
    режиме правки (часть 29, по прямой просьбе владелицы) — по умолчанию теперь присылаю
    компактный пронумерованный список без кнопок под каждой строкой, а кнопки "Править"/
    "Переслать" — под всем списком (см. _send_compact_report/_fetch_employee_report_data)."""
    if config.OWNER_USER_ID is None:
        return
    data = _fetch_employee_report_data(employee_key)
    if data is None:
        label = config.EMPLOYEE_COMMANDS[employee_key]["label"]
        text = f"Не смогла получить задачи «{label}» из ClickUp — попробую в следующий раз."
        try:
            await context.bot.send_message(chat_id=config.OWNER_USER_ID, text=text)
        except Exception:
            logger.exception("Не удалось отправить отчёт по сотруднику %s владелице", employee_key)
        return
    label, scope_note, tasks, include_weekly_button = data
    await _send_compact_report(context, "emp", employee_key, label, scope_note, tasks, include_weekly_button)


def _fetch_employee_report_data(employee_key: str) -> tuple[str, str, list[dict], bool] | None:
    """Живьём тянет данные для _send_employee_report — вынесено отдельно от отправки,
    чтобы дёрнуть те же самые свежие данные из ClickUp повторно, когда владелица нажимает
    "✏️ Править"/"➡️ Переслать" под уже присланным компактным списком (см.
    handle_report_action_callback, часть 29), без дублирования этой логики в двух местах.
    Возвращает (label, scope_note, tasks, include_weekly_button) или None при ошибке
    ClickUp (сообщение об ошибке в этом случае формирует вызывающий код)."""
    employee = config.EMPLOYEE_COMMANDS[employee_key]
    label = employee["label"]
    assignee_id = employee.get("assignee_id")
    name_prefix = employee.get("name_prefix")
    try:
        tasks = clickup_client.get_open_tasks_team_wide(assignee_id=assignee_id)
    except Exception:
        logger.exception("Не удалось получить задачи «%s» по всему ClickUp", label)
        return None
    if name_prefix:
        tasks = [t for t in tasks if t["name"].strip().lower().startswith(name_prefix)]
    return label, "открытые задачи по всему ClickUp", tasks, True


async def _send_employee_weekly_report(context: ContextTypes.DEFAULT_TYPE, employee_key: str) -> None:
    """/liliweekly /olgaweekly /svetaweekly /ilyaweekly /nazgulweekly /alexweekly /ubweekly
    /marinaweekly /nikolayweekly /nickweekly — по прямой просьбе владелицы (06.09, часть
    24): та же логика, что у _send_employee_report, но ищет задачи этого человека ТОЛЬКО в
    одном конкретном списке ClickUp — "WEEKLY TASKS" в пространстве "РАСПИСАНИЕ" (см.
    config.CLICKUP_LIST_WEEKLY), а не по всему workspace. Список ровно один и заранее
    известен, поэтому используется обычный список-ориентированный
    clickup_client.get_open_tasks (как у /tasksatlas и остальных проектных команд), а не
    get_open_tasks_team_wide."""
    if config.OWNER_USER_ID is None:
        return
    data = _fetch_employee_weekly_report_data(employee_key)
    if data is None:
        label = config.EMPLOYEE_COMMANDS[employee_key]["label"]
        text = f"Не смогла получить задачи «{label}» из WEEKLY TASKS — попробую в следующий раз."
        try:
            await context.bot.send_message(chat_id=config.OWNER_USER_ID, text=text)
        except Exception:
            logger.exception("Не удалось отправить weekly-отчёт по сотруднику %s владелице", employee_key)
        return
    label, scope_note, tasks, include_weekly_button = data
    await _send_compact_report(context, "empw", employee_key, label, scope_note, tasks, include_weekly_button)


def _fetch_employee_weekly_report_data(employee_key: str) -> tuple[str, str, list[dict], bool] | None:
    """Живьём тянет данные для _send_employee_weekly_report — см.
    _fetch_employee_report_data (тот же смысл, для weekly-версии команды)."""
    employee = config.EMPLOYEE_COMMANDS[employee_key]
    label = employee["label"]
    assignee_id = employee.get("assignee_id")
    name_prefix = employee.get("name_prefix")
    try:
        tasks = clickup_client.get_open_tasks(config.CLICKUP_LIST_WEEKLY, assignee_id=assignee_id)
    except Exception:
        logger.exception("Не удалось получить задачи «%s» из WEEKLY TASKS", label)
        return None
    if name_prefix:
        tasks = [t for t in tasks if t["name"].strip().lower().startswith(name_prefix)]
    return label, "открытые задачи из WEEKLY TASKS", tasks, False


async def _send_weekly_status_report(context: ContextTypes.DEFAULT_TYPE, command_key: str) -> None:
    """/unsorted /atlas /altyn /approval /docsdev /monday /tuesday /wednesday /thursday
    /friday /saturday /sunday (по прямой просьбе владелицы, часть 27, см.
    config.CLICKUP_WEEKLY_STATUS_COMMANDS) — тянет ВСЕ открытые задачи списка WEEKLY
    TASKS с конкретным статусом (фильтр на стороне ClickUp API, см.
    clickup_client.get_open_tasks/statuses), по всем ответственным сразу — в отличие от
    персональных команд по сотрудникам (/lili /olga ...), эти НЕ привязаны к одному
    человеку. Кнопки под задачами (в режиме правки, часть 29) те же 4, что и у остальных
    отчётов (без 5-й "📆 Weekly» — задача и так уже в WEEKLY TASKS, переносить её ещё раз
    некуда)."""
    if config.OWNER_USER_ID is None:
        return
    data = _fetch_weekly_status_report_data(command_key)
    if data is None:
        label = config.CLICKUP_WEEKLY_STATUS_COMMANDS[command_key]["label"]
        text = f"Не смогла получить задачи «{label}» из WEEKLY TASKS — попробую в следующий раз."
        try:
            await context.bot.send_message(chat_id=config.OWNER_USER_ID, text=text)
        except Exception:
            logger.exception("Не удалось отправить отчёт по статусу WEEKLY TASKS %s владелице", command_key)
        return
    label, scope_note, tasks, include_weekly_button = data
    await _send_compact_report(context, "ws", command_key, label, scope_note, tasks, include_weekly_button)


def _fetch_weekly_status_report_data(command_key: str) -> tuple[str, str, list[dict], bool] | None:
    """Живьём тянет данные для _send_weekly_status_report — см.
    _fetch_employee_report_data (тот же смысл, для команд по статусам WEEKLY TASKS)."""
    command = config.CLICKUP_WEEKLY_STATUS_COMMANDS[command_key]
    label = command["label"]
    status = command["status"]
    try:
        tasks = clickup_client.get_open_tasks(config.CLICKUP_LIST_WEEKLY, statuses=[status])
    except Exception:
        logger.exception("Не удалось получить задачи WEEKLY TASKS со статусом «%s»", status)
        return None
    return label, f"из WEEKLY TASKS · статус «{label}»", tasks, False


_REPORT_KIND_FETCHERS = {
    "emp": _fetch_employee_report_data,
    "empw": _fetch_employee_weekly_report_data,
    "ws": _fetch_weekly_status_report_data,
}


def _fetch_report_data(kind: str, key: str) -> tuple[str, str, list[dict], bool] | None:
    """Общая точка входа для handle_report_action_callback ("✏️ Править"/"➡️ Переслать",
    часть 29) — по kind/key (см. _report_action_keyboard) находит нужную живую функцию из
    _REPORT_KIND_FETCHERS и вызывает её. Неизвестный kind/key (например, старое
    callback_data от уже неактуальной кнопки) — просто None, как и обычная ошибка ClickUp."""
    fetcher = _REPORT_KIND_FETCHERS.get(kind)
    if fetcher is None:
        return None
    try:
        return fetcher(key)
    except KeyError:
        return None


_EMPLOYEE_TASK_ACTIONS = (
    "done", "urgent", "fire", "weekly", "delask", "delyes", "delno", "fwdask", "fwdto", "fwdcancel",
)


async def handle_employee_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Кнопки под задачами в отчётах по сотрудникам (см. _send_employee_report,
    _employee_task_keyboard) — по прямой просьбе владелицы, 06.09-часть 24 (кнопка
    "📆 Weekly" и тег вместо локальной пометки у "🔥 Горит" — часть 27):
    "✅ Сделано" — закрывает задачу в ClickUp (см. clickup_client.mark_task_done —
    сама разбирается, каким именно статусом закрывать конкретный список задачи).
    "🔴 Срочная" — ставит приоритет Urgent в ClickUp (тот же 🔴, что уже используется в
    остальных отчётах для срочных/высокоприоритетных задач).
    "🔥 Горит" — переключатель, ставящий/снимающий НАСТОЯЩИЙ тег ClickUp
    config.CLICKUP_FIRE_TAG_NAME ("кричащая задача», см. _is_fire/
    clickup_client.ensure_tag_on_task) — виден и в веб-интерфейсе ClickUp, не только в
    боте (с части 27; в части 24 это была чисто локальная пометка внутри бота).
    "📆 Weekly" (только там, где включена — см. _employee_task_keyboard) — переносит
    задачу в список WEEKLY TASKS и ставит статус Unsorted (clickup_client.move_task_to_list
    + set_task_status).
    "🗑 Удалить" — двухшаговое действие: сначала "delask" присылает отдельное
    сообщение-подтверждение с именем задачи ("delyes"/"delno"), и только "delyes" реально
    удаляет задачу из ClickUp НАСОВСЕМ — шаг подтверждения добавлен по прямой просьбе
    владелицы (риск случайного нажатия на маленькой кнопке в телефоне на необратимое
    действие).
    "➡️ Переслать" (часть 29) — тоже двухшаговое: "fwdask" показывает список сотрудников,
    у кого известен Telegram id (см. _available_forward_recipients), "fwdto" пересылает
    ИМЕННО ЭТУ задачу выбранному сотруднику, "fwdcancel" — отмена.
    Только для владелицы — тот же общий паттерн проверки, что и у остальных callback-
    кнопок бота (см. handle_escalation_callback)."""
    query = update.callback_query
    if config.OWNER_USER_ID is not None and query.from_user.id != config.OWNER_USER_ID:
        await query.answer()
        return

    _, _, rest = (query.data or "").partition(":")
    rest_parts = rest.split(":")
    action = rest_parts[0] if rest_parts else ""
    task_id = rest_parts[1] if len(rest_parts) > 1 else ""
    extra = rest_parts[2] if len(rest_parts) > 2 else ""
    if action not in _EMPLOYEE_TASK_ACTIONS or not task_id:
        await query.answer()
        return

    if action == "done":
        try:
            clickup_client.mark_task_done(task_id)
        except Exception:
            logger.exception("Не удалось закрыть задачу %s из отчёта по сотруднику", task_id)
            await query.answer("Не смогла отметить как сделано — проверь в ClickUp.", show_alert=True)
            return
        await query.answer("✅ Отмечено как сделано в ClickUp")
        return

    if action == "urgent":
        try:
            clickup_client.set_task_priority(task_id, "urgent")
        except Exception:
            logger.exception("Не удалось поставить приоритет задаче %s из отчёта по сотруднику", task_id)
            await query.answer("Не смогла поставить приоритет — проверь в ClickUp.", show_alert=True)
            return
        await query.answer("🔴 Помечено как срочное в ClickUp")
        return

    if action == "fire":
        try:
            task = clickup_client.get_task(task_id)
        except Exception:
            logger.exception("Не удалось прочитать задачу %s перед пометкой «горит»", task_id)
            await query.answer("Не смогла проверить тег в ClickUp.", show_alert=True)
            return
        if not task:
            await query.answer("Задача не найдена (возможно, уже удалена).", show_alert=True)
            return
        tag_name = config.CLICKUP_FIRE_TAG_NAME
        has_fire = any((tg or "").lower() == tag_name.lower() for tg in task.get("tags") or [])
        try:
            if has_fire:
                clickup_client.remove_tag_from_task(task_id, tag_name)
            else:
                clickup_client.ensure_tag_on_task(task_id, tag_name, space_id=task.get("space_id"))
        except Exception:
            logger.exception(
                "Не удалось %s тег «%s» задаче %s", "снять" if has_fire else "поставить", tag_name, task_id
            )
            await query.answer("Не смогла обновить тег в ClickUp.", show_alert=True)
            return
        if has_fire:
            await query.answer("Сняла тег 🔥")
        else:
            await query.answer(f"🔥 Поставила тег «{tag_name}» в ClickUp")
        return

    if action == "weekly":
        if not config.CLICKUP_WEEKLY_ENABLED:
            await query.answer("Список WEEKLY TASKS пока не настроен.", show_alert=True)
            return
        try:
            clickup_client.move_task_to_list(task_id, config.CLICKUP_LIST_WEEKLY)
            clickup_client.set_task_status(task_id, "unsorted")
        except Exception:
            logger.exception("Не удалось перенести задачу %s в WEEKLY TASKS", task_id)
            await query.answer("Не смогла перенести задачу — проверь в ClickUp.", show_alert=True)
            return
        await query.answer("📆 Перенесла в WEEKLY TASKS, статус Unsorted")
        return

    if action == "fwdask":
        await query.answer()
        recipients = _available_forward_recipients()
        if not recipients:
            await context.bot.send_message(chat_id=config.OWNER_USER_ID, text=_no_forward_recipients_text())
            return
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(rlabel, callback_data=f"emp:fwdto:{task_id}:{rk}")] for rk, rlabel in recipients]
            + [[InlineKeyboardButton("Отмена", callback_data=f"emp:fwdcancel:{task_id}")]]
        )
        await context.bot.send_message(
            chat_id=config.OWNER_USER_ID, text="Кому переслать эту задачу?", reply_markup=keyboard
        )
        return

    if action == "fwdto":
        await query.answer()
        recipient = config.EMPLOYEE_COMMANDS.get(extra)
        recipient_chat_id = _resolve_employee_telegram_id(extra) if recipient else None
        if not recipient or not recipient_chat_id:
            await query.edit_message_text("У этого человека пока не настроен Telegram id.")
            return
        try:
            task = clickup_client.get_task(task_id)
        except Exception:
            logger.exception("Не удалось прочитать задачу %s перед пересылкой", task_id)
            await query.edit_message_text("Не смогла получить задачу для пересылки — проверь в ClickUp.")
            return
        if not task:
            await query.edit_message_text("Задача не найдена (возможно, уже удалена).")
            return
        line = _format_employee_task_lines([task], start_index=1)[0]
        try:
            await context.bot.send_message(chat_id=recipient_chat_id, text=f"📤 Марина переслала задачу:\n{line}")
        except Exception:
            logger.exception("Не удалось переслать задачу %s пользователю %s", task_id, extra)
            await query.edit_message_text("Не смогла переслать — проверь, писал ли этот человек боту раньше.")
            return
        await query.edit_message_text(f"✅ Переслала задачу — {recipient['label']}.")
        return

    if action == "fwdcancel":
        await query.answer()
        await query.edit_message_text("Отменила пересылку.")
        return

    if action == "delask":
        await query.answer()
        try:
            task = clickup_client.get_task(task_id)
        except Exception:
            logger.exception("Не удалось прочитать задачу %s перед удалением", task_id)
            task = None
        task_name = task["name"] if task else task_id
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🗑 Да, удалить насовсем", callback_data=f"emp:delyes:{task_id}"),
                    InlineKeyboardButton("Отмена", callback_data=f"emp:delno:{task_id}"),
                ]
            ]
        )
        await context.bot.send_message(
            chat_id=config.OWNER_USER_ID,
            text=f"Точно удалить эту задачу насовсем из ClickUp?\n«{task_name}»\n\nЭто необратимо.",
            reply_markup=keyboard,
        )
        return

    if action == "delyes":
        try:
            clickup_client.delete_task(task_id)
        except Exception:
            logger.exception("Не удалось удалить задачу %s из отчёта по сотруднику", task_id)
            await query.answer()
            await query.edit_message_text("Не смогла удалить — проверь в ClickUp.")
            return
        await query.answer()
        await query.edit_message_text("🗑 Удалено насовсем.")
        return

    if action == "delno":
        await query.answer()
        await query.edit_message_text("Отменила, задача осталась в ClickUp.")
        return


async def handle_report_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Кнопки "✏️ Править"/"➡️ Переслать" под компактным списком задач (см.
    _send_compact_report/_report_action_keyboard) — по прямой просьбе владелицы, часть 29.
    callback_data: "rpt:edit:<kind>:<key>" / "rpt:fwd:<kind>:<key>" /
    "rpt:fwdto:<kind>:<key>:<recipient_key>" / "rpt:fwdcancel:<kind>:<key>".
    "edit" — заново тянет живые данные (см. _fetch_report_data) и открывает режим правки
    (см. _send_edit_mode_report, задачи партиями по 10 с кнопками под каждой).
    "fwd" — показывает список сотрудников с известным Telegram id (см.
    _available_forward_recipients), "fwdto" пересылает ВЕСЬ список выбранному сотруднику
    (см. _forward_report_to_employee), "fwdcancel" — отмена. Только для владелицы — тот же
    общий паттерн проверки, что и у handle_employee_task_callback."""
    query = update.callback_query
    if config.OWNER_USER_ID is not None and query.from_user.id != config.OWNER_USER_ID:
        await query.answer()
        return

    parts = (query.data or "").split(":")
    if len(parts) < 4 or parts[0] != "rpt":
        await query.answer()
        return
    action, kind, key = parts[1], parts[2], parts[3]
    recipient_key = parts[4] if len(parts) > 4 else ""

    if action == "edit":
        await query.answer()
        data = _fetch_report_data(kind, key)
        if data is None:
            await context.bot.send_message(
                chat_id=config.OWNER_USER_ID, text="Не смогла получить свежие задачи из ClickUp — попробуй ещё раз."
            )
            return
        label, scope_note, tasks, include_weekly_button = data
        await _send_edit_mode_report(context, label, scope_note, tasks, include_weekly_button)
        return

    if action == "fwd":
        await query.answer()
        recipients = _available_forward_recipients()
        if not recipients:
            await context.bot.send_message(chat_id=config.OWNER_USER_ID, text=_no_forward_recipients_text())
            return
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(rlabel, callback_data=f"rpt:fwdto:{kind}:{key}:{rk}")]
                for rk, rlabel in recipients
            ]
            + [[InlineKeyboardButton("Отмена", callback_data=f"rpt:fwdcancel:{kind}:{key}")]]
        )
        await context.bot.send_message(chat_id=config.OWNER_USER_ID, text="Кому переслать список?", reply_markup=keyboard)
        return

    if action == "fwdto":
        await query.answer()
        if not recipient_key:
            return
        await query.edit_message_text("Пересылаю…")
        data = _fetch_report_data(kind, key)
        if data is None:
            await context.bot.send_message(
                chat_id=config.OWNER_USER_ID, text="Не смогла получить свежие задачи из ClickUp — попробуй ещё раз."
            )
            return
        label, scope_note, tasks, _ = data
        await _forward_report_to_employee(context, label, scope_note, tasks, recipient_key)
        return

    if action == "fwdcancel":
        await query.answer()
        await query.edit_message_text("Отменила пересылку.")
        return

    await query.answer()


def _make_employee_command_handler(employee_key: str):
    """Команды /lili /olga /sveta /ilya /nazgul /alex /ub /marina /nikolay /nick — каждая
    для своего человека (см. config.EMPLOYEE_COMMANDS). Только в личке, только для
    владелицы — мгновенно присылает живой отчёт по открытым задачам этого человека по
    всему ClickUp (см. _send_employee_report)."""
    label = config.EMPLOYEE_COMMANDS[employee_key]["label"]

    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        if chat.type != "private":
            await update.message.reply_text("Эта команда работает только в личке.")
            return
        if config.OWNER_USER_ID is None or update.effective_user.id != config.OWNER_USER_ID:
            await update.message.reply_text("Эта команда только для владелицы.")
            return
        if not config.CLICKUP_TEAM_WIDE_ENABLED:
            await update.message.reply_text(
                f"ClickUp workspace-id пока не настроен (CLICKUP_TEAM_ID) — задачи «{label}» "
                f"по всему ClickUp выгружать не могу."
            )
            return
        await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)
        await _send_employee_report(context, employee_key)

    return handler


def _make_employee_weekly_command_handler(employee_key: str):
    """Команды /liliweekly /olgaweekly /svetaweekly /ilyaweekly /nazgulweekly /alexweekly
    /ubweekly /marinaweekly /nikolayweekly /nickweekly (по прямой просьбе владелицы,
    06.09, часть 24) — та же связка, что и _make_employee_command_handler, но для
    weekly-версии отчёта (см. _send_employee_weekly_report, только список WEEKLY TASKS,
    а не весь ClickUp)."""
    label = config.EMPLOYEE_COMMANDS[employee_key]["label"]

    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        if chat.type != "private":
            await update.message.reply_text("Эта команда работает только в личке.")
            return
        if config.OWNER_USER_ID is None or update.effective_user.id != config.OWNER_USER_ID:
            await update.message.reply_text("Эта команда только для владелицы.")
            return
        if not config.CLICKUP_WEEKLY_ENABLED:
            await update.message.reply_text(
                "Список WEEKLY TASKS пока не настроен (CLICKUP_LIST_WEEKLY) — "
                f"задачи «{label}» из него выгружать не могу."
            )
            return
        await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)
        await _send_employee_weekly_report(context, employee_key)

    return handler


def _make_altyn_registry_command_handler(manager_key: str):
    """Команды /altynilya /altynliliana /altynlena /altynslava /altynsveta /altynsergey
    (по прямой просьбе владелицы, часть 32, см. config.ALTYN_MANAGER_COMMANDS) — статусы
    по банкам этого менеджера из реестров Алтына в Google Sheets (см. altyn_registry.py).
    НЕ путать с уже существующими /altyn /atlas (config.CLICKUP_WEEKLY_STATUS_COMMANDS) —
    те про статус задач в ClickUp-списке WEEKLY TASKS, это про банковские реестры, разные
    источники данных, разные команды, совпадений в именах нет. Только в личке, только для
    владелицы, как и остальные отчётные команды."""
    label = config.ALTYN_MANAGER_COMMANDS[manager_key]["label"]

    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        if chat.type != "private":
            await update.message.reply_text("Эта команда работает только в личке.")
            return
        if config.OWNER_USER_ID is None or update.effective_user.id != config.OWNER_USER_ID:
            await update.message.reply_text("Эта команда только для владелицы.")
            return
        await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)
        try:
            rows = altyn_registry.fetch_manager_report(manager_key)
        except Exception:
            logger.exception("Не удалось получить реестр Алтына для менеджера %s", label)
            await update.message.reply_text(
                f"Не смогла прочитать реестры Алтына для «{label}» — проблема с доступом "
                f"к гугл-таблице или сетью, попробуй ещё раз чуть позже."
            )
            return
        text = altyn_registry.format_manager_report(label, rows)
        for chunk in _split_for_telegram(text):
            await update.message.reply_text(chunk)

    return handler


def _make_weekly_status_command_handler(command_key: str):
    """Команды /unsorted /atlas /altyn /approval /docsdev /monday ... /sunday (по прямой
    просьбе владелицы, часть 27, см. config.CLICKUP_WEEKLY_STATUS_COMMANDS) — каждая для
    своего статуса списка WEEKLY TASKS, по всем ответственным сразу. Только в личке,
    только для владелицы — тот же паттерн гейтинга, что у персональных команд по
    сотрудникам."""
    label = config.CLICKUP_WEEKLY_STATUS_COMMANDS[command_key]["label"]

    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        if chat.type != "private":
            await update.message.reply_text("Эта команда работает только в личке.")
            return
        if config.OWNER_USER_ID is None or update.effective_user.id != config.OWNER_USER_ID:
            await update.message.reply_text("Эта команда только для владелицы.")
            return
        if not config.CLICKUP_WEEKLY_ENABLED:
            await update.message.reply_text(
                "Список WEEKLY TASKS пока не настроен (CLICKUP_LIST_WEEKLY) — "
                f"задачи «{label}» из него выгружать не могу."
            )
            return
        await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)
        await _send_weekly_status_report(context, command_key)

    return handler


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
    привязки — классифицируются по отдельности, а то, что не удалось классифицировать —
    сразу в "Разобрать", без вопроса в чат (см. _flush_chat_to_clickup, часть 33)."""
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


async def periodic_memory_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Фоновое обновление "памяти" групповых чатов (по расписанию
    MEMORY_UPDATE_INTERVAL_MINUTES, см. config.py) — по прямой просьбе владелицы (06.09),
    чтобы черновики ответов (см. escalation.draft_initial_answer, chat_memory.py)
    учитывали более раннюю переписку каждого чата. Не зависит от config.CLICKUP_ENABLED —
    память нужна для эскалаций (draft_initial_answer), а не для выгрузки в ClickUp, так
    что работает даже если ClickUp вообще не настроен. Обходит только чаты, где реально
    накопились новые сообщения с прошлого обновления (см.
    storage.get_chats_with_new_messages_for_memory), лучшим усилием — сбой по одному чату
    (сеть, лимиты Claude) не прерывает обработку остальных."""
    for chat_id, chat_title in storage.get_chats_with_new_messages_for_memory():
        try:
            chat_memory.update_chat_memory(chat_id, chat_title)
        except Exception:
            logger.exception("Не удалось обновить память чата %s («%s»)", chat_id, chat_title)


async def handle_commands_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/commands — по прямой просьбе владелицы (06.09, часть 24): краткая справка по ВСЕМ
    командам бота со сжатым описанием, что каждая делает. Собирается по большей части
    динамически из config.CLICKUP_PROJECTS/config.EMPLOYEE_COMMANDS, чтобы список сам
    оставался в курсе, если позже добавятся новые проекты/сотрудники — не нужно отдельно
    помнить про обновление этой справки. Только в личке, только для владелицы, как и
    почти все остальные "технические" команды бота."""
    chat = update.effective_chat
    if chat.type != "private":
        await update.message.reply_text("Эта команда работает только в личке.")
        return
    if config.OWNER_USER_ID is None or update.effective_user.id != config.OWNER_USER_ID:
        await update.message.reply_text("Эта команда только для владелицы.")
        return

    sections = [
        "📋 Список команд Marina Twin\n\n"
        "🤖 Личное:\n"
        "/start — поздороваться / перезапустить бота\n"
        "/reset — сбросить историю личного разговора с ботом\n"
        "/commands — этот список"
    ]

    project_lines = [
        f"/{p['command']} — открытые задачи проекта «{p['label']}» (плюс закрепляет чат за проектом)"
        for p in config.CLICKUP_PROJECTS.values()
        if p.get("command")
    ]
    sections.append(
        "📋 Задачи по проектам ClickUp (вызывать в групповом чате):\n"
        + "\n".join(project_lines)
        + "\n\n(эти же — из личных сообщений, живой отчёт владелице):\n"
        "/tasksall — все проекты одним отчётом\n"
        "/urgent — только срочные задачи по всем проектам"
    )

    employee_lines = [
        f"/{key} — открытые задачи «{e['label']}» по всему ClickUp"
        for key, e in config.EMPLOYEE_COMMANDS.items()
    ]
    sections.append(
        "👤 Задачи по сотрудникам (весь ClickUp, список + кнопки «Править»/«Переслать» внизу):\n"
        + "\n".join(employee_lines)
    )

    weekly_lines = [
        f"/{key}weekly — то же самое, но только из списка WEEKLY TASKS"
        for key in config.EMPLOYEE_COMMANDS
    ]
    sections.append("📅 Те же люди, но только недельные задачи (список WEEKLY TASKS):\n" + "\n".join(weekly_lines))

    weekly_status_lines = [
        f"/{key} — задачи WEEKLY TASKS со статусом «{c['label']}», по всем сразу"
        for key, c in config.CLICKUP_WEEKLY_STATUS_COMMANDS.items()
    ]
    sections.append(
        "📆 Задачи WEEKLY TASKS по статусу (список + кнопки «Править»/«Переслать» внизу):\n"
        + "\n".join(weekly_status_lines)
    )

    altyn_registry_lines = [
        f"/{key} — банки Алтына (Брокер + Кошелек Алтын + Банки РФ) по менеджеру «{c['label']}»"
        for key, c in config.ALTYN_MANAGER_COMMANDS.items()
    ]
    sections.append(
        "🏦 Реестры банков Алтына по менеджеру (живьём из Google Sheets, не путать с "
        "/altyn выше — тот про статус задач ClickUp):\n" + "\n".join(altyn_registry_lines)
    )

    sections.append(
        "🗓 Календарь и прочее:\n"
        "/calendar — события календаря по периодам (сегодня/завтра/неделя/месяц)\n"
        "/cancelall — снять все висящие вопросы из групповых чатов, на которые ещё не ответила\n"
        "/stop — остановить рассылку задач в режиме правки, если нажала по ошибке"
    )

    if config.SCHEDULE_REMINDERS_ENABLED:
        trello_note = "" if config.TRELLO_ENABLED else " (личное расписание из Trello пока не подключено)"
        sections.append(
            "🔔 Напоминания о расписании (без команды, работает автоматически):\n"
            f"— утренний план на день в {config.MORNING_PLAN_HOUR:02d}:{config.MORNING_PLAN_MINUTE:02d}\n"
            f"— точечные напоминания за {', '.join(str(m) for m in config.REMINDER_LEAD_MINUTES)} мин. до "
            f"встречи/задачи с известным временем — из календаря и рабочего расписания (WEEKLY TASKS)" + trello_note
        )

    text = "\n\n".join(sections)
    for chunk in _split_for_telegram(text):
        await context.bot.send_message(chat_id=config.OWNER_USER_ID, text=chunk)


def build_application() -> Application:
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("reset", handle_reset))
    # /urgent — только в личке, только владелице: живая сводка срочных задач по всем
    # проектам сразу (см. handle_urgent_command / _send_urgent_report).
    app.add_handler(CommandHandler("urgent", handle_urgent_command))
    # /cancelall — только в личке, только владелице: снимает разом все висящие вопросы
    # из групп, на которые она ещё не ответила через бота (см. handle_cancelall_command).
    app.add_handler(CommandHandler("cancelall", handle_cancelall_command))
    # /stop — только в личке, только владелице (по прямой просьбе владелицы, часть 33):
    # прерывает рассылку режима правки, если её нажали по ошибке (см.
    # handle_stop_command/_send_edit_mode_report).
    app.add_handler(CommandHandler("stop", handle_stop_command))
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
    app.add_handler(
        CallbackQueryHandler(
            handle_escalation_callback,
            pattern=r"^esc_(confirm_anyway|edited_rewrite|confirm|cancel|retry|own):",
        )
    )
    # Кнопки "Добавить"/"Не добавлять" под черновиком встречи (Google Calendar).
    app.add_handler(
        CallbackQueryHandler(handle_calendar_callback, pattern=r"^cal_(confirm|cancel|edit):")
    )
    # /calendar — только в личке, только владелице: кнопки периода + живой список
    # событий из Google Calendar за выбранный период (см. handle_calendar_command /
    # handle_calendar_view_callback).
    app.add_handler(CommandHandler("calendar", handle_calendar_command))
    app.add_handler(CallbackQueryHandler(handle_calendar_view_callback, pattern=r"^calview:"))
    # Персональные команды по сотрудникам: /lili /olga /sveta /ilya /nazgul /alex /ub /marina
    # /nikolay /nick — только в личке, только владелице (см. config.EMPLOYEE_COMMANDS /
    # _send_employee_report). Плюс для каждого — "weekly"-версия (например
    # "/nikolayweekly", см. _send_employee_weekly_report) — задачи только из списка
    # WEEKLY TASKS (config.CLICKUP_LIST_WEEKLY), а не по всему workspace.
    for employee_key in config.EMPLOYEE_COMMANDS:
        app.add_handler(CommandHandler(employee_key, _make_employee_command_handler(employee_key)))
        app.add_handler(
            CommandHandler(f"{employee_key}weekly", _make_employee_weekly_command_handler(employee_key))
        )
    # /unsorted /atlas /altyn /approval /docsdev /monday ... /sunday — по прямой просьбе
    # владелицы, часть 27 (см. config.CLICKUP_WEEKLY_STATUS_COMMANDS/
    # _send_weekly_status_report): задачи списка WEEKLY TASKS по конкретному статусу, по
    # всем ответственным сразу.
    for command_key in config.CLICKUP_WEEKLY_STATUS_COMMANDS:
        app.add_handler(CommandHandler(command_key, _make_weekly_status_command_handler(command_key)))
    # /altynilya /altynliliana /altynlena /altynslava /altynsveta /altynsergey — по прямой
    # просьбе владелицы, часть 32 (см. config.ALTYN_MANAGER_COMMANDS/altyn_registry.py):
    # статусы по банкам Алтына по каждому менеджеру, живьём из Google Sheets.
    for manager_key in config.ALTYN_MANAGER_COMMANDS:
        app.add_handler(CommandHandler(manager_key, _make_altyn_registry_command_handler(manager_key)))
    # /commands — только в личке, только владелице: краткая справка по всем командам бота
    # (см. handle_commands_command).
    app.add_handler(CommandHandler("commands", handle_commands_command))
    # Кнопки под задачами в РЕЖИМЕ ПРАВКИ отчётов по сотрудникам (✅/🗑/➡️/🔴/🔥, плюс
    # 📆 Weekly в командах по сотрудникам без "weekly" — см. _employee_task_keyboard/
    # handle_employee_task_callback; "➡️ Переслать" — часть 29).
    app.add_handler(
        CallbackQueryHandler(
            handle_employee_task_callback,
            pattern=r"^emp:(done|urgent|fire|weekly|delask|delyes|delno|fwdask|fwdto|fwdcancel):",
        )
    )
    # Кнопки "✏️ Править"/"➡️ Переслать" под компактным списком задач по умолчанию (по
    # прямой просьбе владелицы, часть 29, см. _send_compact_report/
    # handle_report_action_callback).
    app.add_handler(CallbackQueryHandler(handle_report_action_callback, pattern=r"^rpt:"))
    # Кнопки "❌ Отменить"/"✅ Создать" под превью явной команды на постановку задачи в
    # конкретный список/статус (см. _propose_explicit_task_command/handle_manual_task_callback,
    # по прямой просьбе владелицы, 06.09).
    app.add_handler(
        CallbackQueryHandler(handle_manual_task_callback, pattern=r"^mtask_(confirm|cancel):")
    )
    # Личка — обычный разговор с персоной Marina Twin.
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_message))
    # Группы — тихий сбор переписки, без ответов.
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS, handle_group_message))

    # Память групповых чатов (см. chat_memory.py, periodic_memory_job) обновляется всегда,
    # независимо от того, включён ли ClickUp — она нужна для черновиков ответов
    # (escalation.draft_initial_answer), а не для выгрузки задач.
    memory_interval = config.MEMORY_UPDATE_INTERVAL_MINUTES * 60
    app.job_queue.run_repeating(periodic_memory_job, interval=memory_interval, first=memory_interval)
    logger.info("Память групповых чатов включена, обновление каждые %d мин.", config.MEMORY_UPDATE_INTERVAL_MINUTES)

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

    if config.SCHEDULE_REMINDERS_ENABLED:
        reminder_interval = config.REMINDER_CHECK_INTERVAL_MINUTES * 60
        app.job_queue.run_repeating(
            schedule_reminders.check_and_send_reminders_job, interval=reminder_interval, first=reminder_interval
        )
        app.job_queue.run_daily(
            schedule_reminders.morning_plan_job,
            time=digest_time(
                hour=config.MORNING_PLAN_HOUR,
                minute=config.MORNING_PLAN_MINUTE,
                tzinfo=ZoneInfo(config.MARINATWIN_TIMEZONE),
            ),
        )
        logger.info("Напоминания о расписании включены.")
    else:
        logger.info("Напоминания о расписании выключены.")

    return app


def main() -> None:
    # claude_client уже при импорте выше загрузил базу знаний (см. kb.load_core внутри него)
    logger.info(
        "База загружена, запускаю бота (модель: %s, лёгкая модель: %s)",
        config.MODEL_NAME,
        config.LIGHT_MODEL_NAME,
    )
    app = build_application()
    app.run_polling()


if __name__ == "__main__":
    main()
