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
