"""Бронирование встречи после /calendarfree (04.10.2026, по прямой просьбе владелицы).
После того как человек увидел свободные слоты, бот спрашивает «Вы бы хотели запланировать
встречу?» (Да / Нет). По «Да» просит написать дату и время в формате «ДД.ММ.ГГ в ЧЧ:ММ»
(пример: 9.10.26 в 14:00), проверяет, что час свободен в основном календаре владелицы
(config.GOOGLE_CALENDAR_ID) и укладывается в 8:00-20:00, показывает итог с кнопкой
«Подтвердить» и только после неё создаёт событие на 1 час. Событие создаётся приватным
(calendar_client.create_event), владелице приходит уведомление в личку.
Работает в личке и в трёх рабочих группах из config.CALENDAR_VIEWER_ALLOWED_CHAT_IDS;
кнопки и ответ датой принимаются только от того, кто запросил слоты.
Модуль отдельный, потому что bot.py запускается как __main__; calendar_free.register(app)
сам вызывает calendar_book.register(app)."""
import asyncio
import html
import logging
import re
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationHandlerStop,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import calendar_client
import calendar_free
import config
logger = logging.getLogger("marina_twin_bot")
STATE_KEY = "cfree_book"
COUNT_KEY = "cfree_book_count"
STATE_TTL = 900
MEETING_MINUTES = 60
MAX_DAYS_AHEAD = 60
MAX_BOOKINGS_PER_DAY = 3
QUESTION_TEXT = "Вы бы хотели запланировать встречу?"
_WHEN_RE = re.compile(
    r"^\s*(\d{1,2})[./](\d{1,2})[./](\d{4}|\d{2})\s*(?:в|,)?\s*(\d{1,2})[:.](\d{2})\s*(?:мск|msk)?\s*$",
    re.IGNORECASE,
)
def parse_when(text: str, tz: ZoneInfo, now: datetime) -> datetime:
    """Разбирает «9.10.26 в 14:00» в datetime с таймзоной. ValueError(текст для человека)."""
    m = _WHEN_RE.match(text or "")
    if not m:
        raise ValueError("Не получилось разобрать дату и время.")
    day, month, year, hour, minute = m.groups()
    year_i = int(year)
    if year_i < 100:
        year_i += 2000
    try:
        start = datetime(year_i, int(month), int(day), int(hour), int(minute), tzinfo=tz)
    except ValueError:
        raise ValueError("Такой даты или времени не существует.") from None
    if start <= now:
        raise ValueError("Это время уже прошло.")
    if start.date() > now.date() + timedelta(days=MAX_DAYS_AHEAD):
        raise ValueError(f"Записаться можно максимум на {MAX_DAYS_AHEAD} дней вперёд.")
    return start
def check_slot(start: datetime, busy: list, tz: ZoneInfo, now: datetime) -> tuple[bool, list]:
    """(свободен ли час с start, свободные окна дня не короче часа)."""
    end = start + timedelta(minutes=MEETING_MINUTES)
    slots = calendar_free.free_slots(start.date(), busy, tz, now)
    ok = any(s <= start and end <= e for s, e in slots)
    long_slots = [(s, e) for s, e in slots if (e - s) >= timedelta(minutes=MEETING_MINUTES)]
    return ok, long_slots
def _tz_label() -> str:
    return "московское время" if config.MARINATWIN_TIMEZONE == "Europe/Moscow" else config.MARINATWIN_TIMEZONE
def _fmt_day(d: date) -> str:
    return f"{calendar_free.WEEKDAYS[d.weekday()]} {d.strftime('%d.%m.%y')}"
def _slots_text(slots: list) -> str:
    return ", ".join(f"{s.strftime('%H:%M')}-{e.strftime('%H:%M')}" for s, e in slots)
def _prompt_html() -> str:
    return (
        "Напишите удобные дату и время одним сообщением в формате:\n"
        "<b>ДД.ММ.ГГ в ЧЧ:ММ</b>\n"
        "Например: <code>9.10.26 в 14:00</code>\n\n"
        f"Встреча длится 1 час, {_tz_label()}, рабочие часы 8:00-20:00. "
        "Потом останется нажать «Подтвердить»."
    )


def _kb(uid: int, *pairs) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=f"cfbk:{action}:{uid}") for label, action in pairs]])


def _yes_no_kb(uid: int) -> InlineKeyboardMarkup:
    return _kb(uid, ("Да", "yes"), ("Нет", "no"))


def _await_kb(uid: int) -> InlineKeyboardMarkup:
    return _kb(uid, ("Отмена", "cancel"))


def _confirm_kb(uid: int) -> InlineKeyboardMarkup:
    return _kb(uid, ("Подтвердить", "ok"), ("Другое время", "redo"), ("Отмена", "cancel"))


TOPIC_MAX = 100


def _topic_kb(uid: int) -> InlineKeyboardMarkup:
    return _kb(uid, ("Без темы", "notopic"), ("Отмена", "cancel"))


def _confirm_text(state: dict) -> str:
    start = datetime.fromisoformat(state["start"])
    end = start + timedelta(minutes=MEETING_MINUTES)
    when = f"{_fmt_day(start.date())}, {start.strftime('%H:%M')}-{end.strftime('%H:%M')}"
    topic = state.get("topic") or "без темы"
    return f"Записать встречу на {when} ({_tz_label()})? Длительность 1 час.\nТема: {topic}"


def _states(context) -> dict:
    return context.application.bot_data.setdefault(STATE_KEY, {})


def _purge(states: dict) -> None:
    now = time.time()
    for key in [k for k, v in states.items() if now - v["ts"] > STATE_TTL]:
        states.pop(key, None)


def _bookings_left(context, uid: int) -> int:
    counts = context.application.bot_data.setdefault(COUNT_KEY, {})
    recent = [t for t in counts.get(uid, []) if time.time() - t < 86400]
    counts[uid] = recent
    return MAX_BOOKINGS_PER_DAY - len(recent)


async def _day_busy(start: datetime, tz: ZoneInfo) -> list:
    day_start = datetime.combine(start.date(), datetime.min.time(), tz)
    events = await asyncio.to_thread(
        calendar_client.list_events, day_start.isoformat(), (day_start + timedelta(days=1)).isoformat()
    )
    return calendar_free._parse_busy(events, tz)


async def offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Вызывается из calendar_free после показа слотов: задаёт вопрос про встречу."""
    query = update.callback_query
    chat = update.effective_chat
    if query is None or chat is None or not config.GOOGLE_CALENDAR_ENABLED:
        return
    uid = query.from_user.id
    states = _states(context)
    _purge(states)
    old = states.pop((chat.id, uid), None)
    if old and old.get("msg_id"):
        try:
            await context.bot.delete_message(chat_id=chat.id, message_id=old["msg_id"])
        except Exception:
            pass
    sent = await query.message.reply_text(QUESTION_TEXT, reply_markup=_yes_no_kb(uid))
    states[(chat.id, uid)] = {"stage": "offer", "ts": time.time(), "msg_id": sent.message_id}


async def handle_book_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    chat = update.effective_chat
    parts = (query.data or "").split(":")
    if len(parts) != 3 or chat is None or not calendar_free._allowed_chat(chat):
        await query.answer()
        return
    _, action, uid_s = parts
    user = query.from_user
    if str(user.id) != uid_s:
        await query.answer("Эти кнопки для другого участника. Запросите /calendarfree сами.", show_alert=True)
        return
    await query.answer()
    states = _states(context)
    key = (chat.id, user.id)
    state = states.get(key)
    if action in ("no", "cancel"):
        states.pop(key, None)
        await query.edit_message_text("Хорошо. Если понадобится, напишите /calendarfree.")
        return
    if state is None or time.time() - state["ts"] > STATE_TTL:
        states.pop(key, None)
        await query.edit_message_text("Запрос устарел. Напишите /calendarfree и выберите период заново.")
        return
    tz = ZoneInfo(config.MARINATWIN_TIMEZONE)
    if action in ("yes", "redo"):
        if action == "yes" and _bookings_left(context, user.id) <= 0:
            states.pop(key, None)
            await query.edit_message_text(
                "За сутки уже забронировано максимум встреч. Если нужно ещё, напишите владелице напрямую."
            )
            return
        state.update(stage="await", ts=time.time(), msg_id=query.message.message_id)
        await query.edit_message_text(_prompt_html(), parse_mode="HTML", reply_markup=_await_kb(user.id))
        return
    if action == "notopic" and state.get("stage") == "topic":
        state.update(stage="confirm", topic="", ts=time.time())
        await query.edit_message_text(_confirm_text(state), reply_markup=_confirm_kb(user.id))
        return
    if action == "ok" and state.get("stage") == "confirm":
        await _finish_booking(query, context, chat, user, state, tz)
        return
    await query.edit_message_text("Запрос устарел. Напишите /calendarfree и выберите период заново.")
    states.pop(key, None)


async def _finish_booking(query, context, chat, user, state, tz) -> None:
    states = _states(context)
    key = (chat.id, user.id)
    start = datetime.fromisoformat(state["start"])
    end = start + timedelta(minutes=MEETING_MINUTES)
    now = datetime.now(tz)
    try:
        busy = await _day_busy(start, tz)
    except Exception:
        logger.exception("/calendarfree: не удалось перепроверить календарь перед записью")
        await query.edit_message_text(
            "Не получилось проверить календарь, попробуйте ещё раз чуть позже.", reply_markup=_confirm_kb(user.id)
        )
        return
    ok, long_slots = check_slot(start, busy, tz, now)
    if not ok:
        state.update(stage="await", ts=time.time())
        extra = f"\nСвободные окна на этот день: {_slots_text(long_slots)}." if long_slots else "\nНа этот день свободных окон на час нет."
        await query.edit_message_text(
            "Это время только что заняли или оно уже прошло." + extra + "\n\n" + _prompt_html(),
            parse_mode="HTML",
            reply_markup=_await_kb(user.id),
        )
        return
    name = (user.full_name or user.username or str(user.id))[:60]
    handle = f" (@{user.username})" if user.username else ""
    where = chat.title or "личная переписка с ботом"
    description = f"Записался(лась) через бота: {name}{handle}\nЧат: {where}"
    try:
        await asyncio.to_thread(
            calendar_client.create_event, f"Встреча: {name}", start.isoformat(), end.isoformat(), None, description
        )
    except Exception:
        logger.exception("/calendarfree: не удалось создать событие")
        await query.edit_message_text(
            "Не получилось записать встречу, попробуйте ещё раз чуть позже.", reply_markup=_confirm_kb(user.id)
        )
        return
    states.pop(key, None)
    context.application.bot_data.setdefault(COUNT_KEY, {}).setdefault(user.id, []).append(time.time())
    when = f"{_fmt_day(start.date())}, {start.strftime('%H:%M')}-{end.strftime('%H:%M')}"
    await query.edit_message_text(f"Готово, встреча забронирована: {when} ({_tz_label()}).")
    if config.OWNER_USER_ID is not None and user.id != config.OWNER_USER_ID:
        try:
            await context.bot.send_message(
                chat_id=config.OWNER_USER_ID,
                text=f"Новая запись на встречу через бота: {name}{handle}, {where}. {when}. Событие уже в календаре.",
            )
        except Exception:
            logger.exception("/calendarfree: не удалось уведомить владелицу о записи")


async def handle_when_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ловит ответ с датой и временем от того, кто нажал «Да». Остальные сообщения пропускает."""
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if msg is None or chat is None or user is None or not msg.text:
        return
    states = _states(context)
    key = (chat.id, user.id)
    state = states.get(key)
    if state is not None and state.get("stage") == "topic":
        if time.time() - state["ts"] > STATE_TTL:
            states.pop(key, None)
            return
        topic = " ".join(msg.text.split())
        if len(topic) > TOPIC_MAX:
            await msg.reply_text(
                f"Тема слишком длинная, напишите короче (до {TOPIC_MAX} символов).", reply_markup=_topic_kb(user.id)
            )
            raise ApplicationHandlerStop
        state.update(stage="confirm", topic=topic, ts=time.time())
        sent = await msg.reply_text(_confirm_text(state), reply_markup=_confirm_kb(user.id))
        state["msg_id"] = sent.message_id
        raise ApplicationHandlerStop
    if state is None or state.get("stage") != "await":
        return
    if chat.type != "private" and (len(msg.text) > 40 or not any(c.isdigit() for c in msg.text)):
        return
    if time.time() - state["ts"] > STATE_TTL:
        states.pop(key, None)
        await msg.reply_text("Запрос устарел. Напишите /calendarfree и выберите период заново.")
        raise ApplicationHandlerStop
    tz = ZoneInfo(config.MARINATWIN_TIMEZONE)
    now = datetime.now(tz)
    try:
        start = parse_when(msg.text, tz, now)
    except ValueError as exc:
        await msg.reply_text(f"{exc}\n\n" + _prompt_html(), parse_mode="HTML", reply_markup=_await_kb(user.id))
        raise ApplicationHandlerStop
    try:
        busy = await _day_busy(start, tz)
    except Exception:
        logger.exception("/calendarfree: не удалось проверить календарь для записи")
        await msg.reply_text(
            "Не получилось проверить календарь, попробуйте ещё раз чуть позже.", reply_markup=_await_kb(user.id)
        )
        raise ApplicationHandlerStop
    ok, long_slots = check_slot(start, busy, tz, now)
    if not ok:
        extra = (
            f"Свободные окна на {_fmt_day(start.date())}: {_slots_text(long_slots)}."
            if long_slots
            else f"На {_fmt_day(start.date())} свободных окон на час нет."
        )
        await msg.reply_text(
            "Это время занято или не входит в рабочие часы 8:00-20:00.\n" + extra + "\n\n" + _prompt_html(),
            parse_mode="HTML",
            reply_markup=_await_kb(user.id),
        )
        raise ApplicationHandlerStop
    end = start + timedelta(minutes=MEETING_MINUTES)
    when = f"{_fmt_day(start.date())}, {start.strftime('%H:%M')}-{end.strftime('%H:%M')}"
    sent = await msg.reply_text(
        f"Записать встречу на {when} ({_tz_label()})? Длительность 1 час.",
        reply_markup=_confirm_kb(user.id),
    )
    state.update(stage="confirm", start=start.isoformat(), ts=time.time(), msg_id=sent.message_id)
    raise ApplicationHandlerStop


def register(app) -> None:
    """Регистрирует обработчики записи на встречу.

    Ответ с датой ловится в group=-1, раньше обычной обработки сообщений, чтобы текст
    с датой не уходил в основной диалог бота: после успеха и ошибок поднимается
    ApplicationHandlerStop.
    """
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_when_reply), group=-1)
    app.add_handler(CallbackQueryHandler(handle_book_callback, pattern="^cfbk:"))
