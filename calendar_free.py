"""/calendarfree: свободные слоты в календаре (03.10.2026, по прямой просьбе владелицы).
Команда спрашивает период кнопками (сегодня / завтра / текущая неделя / следующая неделя)
и показывает только СВОБОДНЫЕ окна с 8:00 до 20:00 по каждому дню, считая занятыми все
события основного календаря (config.GOOGLE_CALENDAR_ID) кроме событий на весь день. Для
сегодняшнего дня окна считаются от текущего момента. Только владелица и только в личке.
Модуль отдельный, потому что bot.py запускается как __main__; bot.py вызывает register(app)."""
import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes
import calendar_client
import config

logger = logging.getLogger("marina_twin_bot")

DAY_START_HOUR = 8
DAY_END_HOUR = 20
MIN_SLOT_MINUTES = 15

PERIOD_LABELS = {
    "today": "Сегодня",
    "tomorrow": "Завтра",
    "week": "Текущая неделя",
    "nextweek": "Следующая неделя",
}

WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def _keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Сегодня", callback_data="cfree:today"),
                InlineKeyboardButton("Завтра", callback_data="cfree:tomorrow"),
            ],
            [
                InlineKeyboardButton("Текущая неделя", callback_data="cfree:week"),
                InlineKeyboardButton("Следующая неделя", callback_data="cfree:nextweek"),
            ],
        ]
    )


def period_days(period: str, today: date) -> list[date]:
    """Дни периода. Текущая неделя: от сегодня до воскресенья, следующая: пн-вс."""
    if period == "today":
        return [today]
    if period == "tomorrow":
        return [today + timedelta(days=1)]
    if period == "week":
        return [today + timedelta(days=i) for i in range(7 - today.weekday())]
    if period == "nextweek":
        monday = today + timedelta(days=7 - today.weekday())
        return [monday + timedelta(days=i) for i in range(7)]
    return []


def _parse_busy(events: list[dict], tz: ZoneInfo) -> list[tuple[datetime, datetime]]:
    busy = []
    for e in events:
        if e.get("all_day"):
            continue
        try:
            start = datetime.fromisoformat(e["start"]).astimezone(tz)
            end = datetime.fromisoformat(e["end"]).astimezone(tz)
        except (KeyError, ValueError, TypeError):
            continue
        if end > start:
            busy.append((start, end))
    return busy
