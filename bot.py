"""
Telegram-бот "Marina Twin" — штатный юрист по праву РФ, ВЭД и крипто
в СНГ/Таможенном союзе/ЕАЭС. Интерфейс поверх Claude API с кэшированной базой
знаний и точечной подгрузкой странового модуля по ходу разговора.

Запуск: python bot.py
Нужны переменные окружения: TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY (см. .env.example).
"""

import asyncio
import logging
import random
import re
import time
from datetime import datetime, time as digest_time
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.error import BadRequest
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

_MARINA_NAME_RE = re.compile(r"\bмарин(а|ы|е|у|ой|ою)\b|\bmar[iy]na\b|\bmary\b", re.IGNORECASE)

_ACK_PHRASES = [
    "Секунду, уточню и вернусь 🙂",
    "Дай мне минутку — уточню и отвечу.",
    "Сейчас, только уточню детали — и сразу вернусь с ответом.",
]

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
) -> None:
    try:
        draft = escalation.draft_initial_answer(group_title, asker_name, question, project_key)
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
        try:
            draft = escalation.draft_initial_answer(esc["group_title"], esc["asker_name"], esc["question"])
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
        pending = storage.get_oldest_pending_escalation()
        if pending:
            esc = storage.get_escalation(pending[0])
            if esc:
                await _handle_owner_escalation_message(update, context, esc, text)
                return
        # Обычное сообщение владелицы в личке (не reply на эскалацию) — помимо ответа
        # Twin ниже, заодно проверяем, не задача ли это, и если да — заносим в ClickUp
        # (см. _log_owner_dm_tasks). Только для самой владелицы: у остальных пользователей
        # в личке — просто разговор с Twin, их сообщения в ClickUp не идут.
        await _log_owner_dm_tasks(user, text)

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
    отвечает "сейчас вернусь" и пересылает вопрос владелице в личку (см. handle_message);
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
    text = msg.text or ""
    if not text.strip():
        return

    if update.edited_message is not None:
        await _handle_group_message_edited(chat, msg, text)
        return

    # Ответ на уточняющий вопрос "Atlas, Altyn или BestSwift?" (см.
    # _ask_classification_question) — проверяем в первую очередь, это отдельный поток
    # от привязки чата и обращения к "Марине" ниже.
    reply_to = msg.reply_to_message
    if reply_to:
        classification = storage.get_classification_by_question_message_id(chat.id, reply_to.message_id)
        if classification:
            await _resolve_classification_reply(update, context, classification, text)
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
            await msg.reply_text(random.choice(_ACK_PHRASES))
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
                context, esc_id, group_title, asker_name, question_text, project_key, asker_username
            )
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



def _resolve_assignee_id(name: str | None) -> int | None:
    """Пытается сопоставить имя ответственного (как его назвал Claude в task_extractor.py,
    поле assignee_name) с ClickUp user_id по config.CLICKUP_ASSIGNEE_MAP. Осознанно строгое
    сравнение (без нечётких совпадений) — лучше не проставить Assignee, чем назначить не
    тому человеку. Пусто/нет совпадения — None, вызывающий код просто не передаёт assignees."""
    if not name:
        return None
    return config.CLICKUP_ASSIGNEE_MAP.get(name.strip().lower())


def _create_and_log_task(
    chat_id: int,
    chat_title: str,
    project_key: str,
    title: str,
    description: str,
    priority,
    assignee_id: int | None = None,
) -> str | None:
    """Создаёт одну задачу в ClickUp-списке project_key и логирует её в pushed_tasks
    (нужно и для отладки, и для отчёта по /tasksX — см. _send_project_report).
    assignee_id — ClickUp user_id ответственного, если удалось сопоставить (см.
    _resolve_assignee_id), иначе None. Возвращает id созданной задачи в ClickUp, либо
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
        assignee_id = _resolve_assignee_id(t.get("assignee_name"))
        if _create_and_log_task(
            chat_id, chat_title, project_key, title, t.get("description", ""), t.get("priority"), assignee_id
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
    try:
        tasks = task_extractor.extract_tasks_classified(
            chat_title, [{"user_name": user.first_name or "Марина", "text": text, "ts": time.time()}]
        )
    except Exception:
        logger.exception("Ошибка извлечения задач из личного сообщения владелицы")
        return
    if not tasks:
        return
    created = _push_tasks(user.id, chat_title, tasks, lambda t: t.get("project") or "unsorted")
    if created:
        logger.info("Из личного сообщения владелицы занесено задач в ClickUp: %s", created)


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
    assignee_id = _resolve_assignee_id(classification.get("task_assignee_name"))

    task_id = _create_and_log_task(
        classification["chat_id"],
        classification["chat_title"],
        project_key,
        classification["task_title"],
        classification["task_description"],
        classification["task_priority"],
        assignee_id,
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
        assignee_id = _resolve_assignee_id(c.get("task_assignee_name"))
        task_id = _create_and_log_task(
            c["chat_id"],
            c["chat_title"],
            "unsorted",
            c["task_title"],
            c["task_description"],
            c["task_priority"],
            assignee_id,
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
    классифицируется отдельно (Atlas/Алтын/BestSwift); неоднозначные не падают молча
    в "Разобрать", а сначала переспрашиваются в чате (см. _ask_classification_question).
    Сериализовано локом на chat_id (см. _get_chat_flush_lock) — защита от гонки между
    немедленной выгрузкой из handle_group_message и периодической (periodic_flush_job)."""
    async with _get_chat_flush_lock(chat_id):
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
                    chat_id, chat_title, title, t.get("description", ""), t.get("priority"), t.get("assignee_name")
                )
                await _ask_classification_question(context, chat_id, chat_title, classification_id, title)
        storage.mark_flushed(chat_id)
        return created


_URGENT_PRIORITIES = {"urgent", "high"}


def _is_urgent(task: dict) -> bool:
    return (task.get("priority") or "") in _URGENT_PRIORITIES


def _format_due_suffix(due_date: float | None) -> str:
    """Возвращает суффикс со сроком «(до ДД.ММ.ГГГГ)» для строки отчёта, если у задачи
    задан срок в ClickUp, иначе пустую строку."""
    if not due_date:
        return ""
    dt = datetime.fromtimestamp(due_date, tz=ZoneInfo(config.MARINATWIN_TIMEZONE))
    return f" (до {dt.strftime('%d.%m.%Y')})"


def _format_task_lines(tasks: list[dict]) -> list[str]:
    """Форматирует список задач ClickUp (см. clickup_client.get_open_tasks) в пронумерованные
    строки отчёта, отмечая срочные/высокоприоритетные задачи значком 🔴 и, если у задачи
    задан срок в ClickUp, дописывая его в конце строки."""
    lines = []
    for i, t in enumerate(tasks, start=1):
        marker = "🔴 " if _is_urgent(t) else ""
        due_suffix = _format_due_suffix(t.get("due_date"))
        lines.append(f"{i}. {marker}{t['name']}{due_suffix}")
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
    app.add_handler(
        CallbackQueryHandler(
            handle_escalation_callback,
            pattern=r"^esc_(confirm_anyway|edited_rewrite|confirm|cancel|retry|own):",
        )
    )
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
    logger.info(
        "База загружена, запускаю бота (модель: %s, лёгкая модель: %s)",
        config.MODEL_NAME,
        config.LIGHT_MODEL_NAME,
    )
    app = build_application()
    app.run_polling()


if __name__ == "__main__":
    main()
