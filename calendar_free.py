"""/calendarfree: свободные слоты в календаре (03.10.2026, по прямой просьбе владелицы).
Команда спрашивает период кнопками (сегодня / завтра / текущая неделя / следующая неделя)
и показывает только СВОБОДНЫЕ окна с 10:00 до 21:00 по каждому дню, считая занятыми все
события основного календаря (config.GOOGLE_CALENDAR_ID) кроме событий на весь день. Для
сегодняшнего дня окна считаются от текущего момента. Доступна всем в личке и участникам трёх рабочих групп (config.CALENDAR_VIEWER_ALLOWED_CHAT_IDS); показывает лишь свободные окна, без названий событий. После слотов предлагает забронировать встречу (calendar_book.py).
Модуль отдельный, потому что bot.py запускается как __main__; bot.py вызывает register(app)."""
import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes
import calendar_client
import config

logger = logging.getLogger("marina_twin_bot")

DAY_START_HOUR = 10
DAY_END_HOUR = 21
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


def _allowed_chat(chat) -> bool:
    """Личка с кем угодно или одна из трёх рабочих групп (config.CALENDAR_VIEWER_ALLOWED_CHAT_IDS)."""
    if chat is None:
        return False
    if chat.type == "private":
        return True
    return chat.id in config.CALENDAR_VIEWER_ALLOWED_CHAT_IDS


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


def free_slots(day: date, busy: list[tuple[datetime, datetime]], tz: ZoneInfo, now: datetime) -> list[tuple[datetime, datetime]]:
    """Свободные окна дня между DAY_START_HOUR и DAY_END_HOUR не короче MIN_SLOT_MINUTES.
    Для сегодняшнего дня начало сдвигается к ближайшим 15 минутам от текущего момента."""
    win_start = datetime.combine(day, time(DAY_START_HOUR), tz)
    win_end = datetime.combine(day, time(DAY_END_HOUR), tz)
    if day == now.date():
        rounded = now.replace(second=0, microsecond=0)
        rounded += timedelta(minutes=(-rounded.minute) % 15)
        win_start = max(win_start, rounded)
    if win_start >= win_end:
        return []
    clipped = sorted((max(s, win_start), min(e, win_end)) for s, e in busy if e > win_start and s < win_end)
    slots = []
    cursor = win_start
    for s, e in clipped:
        if s > cursor and (s - cursor) >= timedelta(minutes=MIN_SLOT_MINUTES):
            slots.append((cursor, s))
        cursor = max(cursor, e)
    if win_end > cursor and (win_end - cursor) >= timedelta(minutes=MIN_SLOT_MINUTES):
        slots.append((cursor, win_end))
    return slots


def _duration(start: datetime, end: datetime) -> str:
    minutes = int((end - start).total_seconds() // 60)
    hours, rest = divmod(minutes, 60)
    if hours and rest:
        return f"{hours} ч {rest} мин"
    if hours:
        return f"{hours} ч"
    return f"{rest} мин"


def render(period: str, days: list[date], busy: list[tuple[datetime, datetime]], tz: ZoneInfo, now: datetime) -> str:
    lines = [f"Свободные слоты, {PERIOD_LABELS[period].lower()} ({DAY_START_HOUR:02d}:00-{DAY_END_HOUR:02d}:00):"]
    for day in days:
        label = f"{WEEKDAYS[day.weekday()]} {day.strftime('%d.%m')}"
        slots = free_slots(day, busy, tz, now)
        if not slots:
            if day == now.date() and now >= datetime.combine(day, time(DAY_END_HOUR), tz):
                lines.append(f"\n{label}: рабочее время уже закончилось")
            else:
                lines.append(f"\n{label}: свободных окон нет")
            continue
        parts = [f"{s.strftime('%H:%M')}-{e.strftime('%H:%M')} ({_duration(s, e)})" for s, e in slots]
        lines.append(f"\n{label}:\n" + "\n".join(parts))
    return "\n".join(lines)


async def handle_calendarfree_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    if user is None or not _allowed_chat(chat):
        return
    if not config.GOOGLE_CALENDAR_ENABLED:
        await update.message.reply_text("Календарь сейчас не подключён.")
        return
    await update.message.reply_text("За какой период показать свободные слоты?", reply_markup=_keyboard())


async def handle_calendarfree_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat = update.effective_chat
    if not _allowed_chat(chat):
        return
    _, _, period = (query.data or "").partition(":")
    if period not in PERIOD_LABELS:
        return
    tz = ZoneInfo(config.MARINATWIN_TIMEZONE)
    now = datetime.now(tz)
    days = period_days(period, now.date())
    range_start = datetime.combine(days[0], time(0), tz)
    range_end = datetime.combine(days[-1] + timedelta(days=1), time(0), tz)
    try:
        events = calendar_client.list_events(range_start.isoformat(), range_end.isoformat())
    except Exception:
        logger.exception("/calendarfree: не удалось получить события календаря за период %s", period)
        await query.edit_message_text(
            "Не смогла прочитать календарь, попробуй ещё раз чуть позже.", reply_markup=_keyboard()
        )
        return
    text = render(period, days, _parse_busy(events, tz), tz, now)
    try:
        await query.edit_message_text(text[:4000], reply_markup=_keyboard())
    except BadRequest as e:
        if "not modified" not in str(e).lower():
            raise
    try:
        import calendar_book

        await calendar_book.offer(update, context)
    except Exception:
        logger.exception("/calendarfree: не удалось предложить запись на встречу")


def register(app) -> None:
    """Регистрирует /calendarfree и кнопки периода. Вызывать в build_application."""
    app.add_handler(CommandHandler("calendarfree", handle_calendarfree_command))
    app.add_handler(CallbackQueryHandler(handle_calendarfree_callback, pattern=r"^cfree:"))
    import calendar_book

    calendar_book.register(app)
