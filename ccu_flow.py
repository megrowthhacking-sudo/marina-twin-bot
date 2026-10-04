"""Подтверждение перед публикацией для /calendarclickup (03.10.2026, по прямой просьбе
владелицы): бот сначала присылает ПЛАН изменений календаря в личку с кнопками
"✅ Опубликовать" / "✏️ Изменить" / "❌ Отмена", и только после "Опубликовать" пишет в
Google Calendar (clickup_meeting_watch.apply_calendar_actions — единственное место записи).
"Изменить" — владелица присылает правку текстом, план обновляется и показывается снова с
теми же тремя кнопками, и так без ограничений; "Отмена" отменяет команду целиком.
Вынесено из bot.py в отдельный модуль, потому что bot.py запускается как __main__ и не
может быть импортирован отсюда: нужные ему хелперы передаются через bind() (вызывается в
bot.py перед build_application). Планы хранятся в памяти процесса (app.bot_data) и теряются
при рестарте — тогда кнопка отвечает "план уже не актуален"."""
import logging
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes
import calendar_client
import clickup_meeting_watch
import config
logger = logging.getLogger("marina_twin_bot")
_d: dict = {}
def bind(*, period_bounds, period_labels, period_keyboard, format_event_line, split_for_telegram, message_limit) -> None:
    """Передаёт хелперы bot.py (см. комментарий в начале модуля)."""
    _d.update(
        period_bounds=period_bounds,
        period_labels=period_labels,
        period_keyboard=period_keyboard,
        format_event_line=format_event_line,
        split_for_telegram=split_for_telegram,
        message_limit=message_limit,
    )
def get_awaiting(context: ContextTypes.DEFAULT_TYPE):
    """plan_id плана, для которого владелица нажала "Изменить" и теперь присылает правку, либо None."""
    return context.application.bot_data.get(AWAITING_KEY)
def register(app) -> None:
    """Регистрирует обработчики кнопок. Вызывать ДО регистрации старого обработчика "^ccu:"
    в bot.py — побеждает первый подходящий."""
    app.add_handler(CallbackQueryHandler(period_callback, pattern=r"^ccu:"))
    app.add_handler(CallbackQueryHandler(plan_callback, pattern=r"^ccup:"))
PLANS_KEY = "ccu_plans"
AWAITING_KEY = "ccu_awaiting_edit"
MAX_PLANS = 5
def _ccu_plan_keyboard(plan_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Опубликовать", callback_data=f"ccup:pub:{plan_id}"),
                InlineKeyboardButton("✏️ Изменить", callback_data=f"ccup:edit:{plan_id}"),
            ],
            [InlineKeyboardButton("❌ Отмена", callback_data=f"ccup:cancel:{plan_id}")],
        ]
    )
def _ccu_format_event_lines(label: str, events: list[dict]) -> str:
    """Список событий календаря за период тем же форматом, что и /calendar, с обрезкой
    под лимит сообщения Telegram."""
    tz = ZoneInfo(config.MARINATWIN_TIMEZONE)
    if not events:
        return f"\U0001f4c5 {label}: событий нет."
    header = f"\U0001f4c5 {label} ({len(events)}):\n\n"
    body = "\n".join(_d["format_event_line"](e, tz) for e in events)
    if len(header) + len(body) > _d["message_limit"] - 400:
        budget = _d["message_limit"] - 400 - len(header) - 80
        truncated = body[:budget] if budget > 0 else ""
        cut = truncated.rfind("\n")
        if cut != -1:
            truncated = truncated[:cut]
        shown = truncated.count("\n") + 1 if truncated else 0
        body = f"{truncated}\n\n...и ещё {len(events) - shown} событий, не поместились — сузь период."
    return header + body
def _ccu_render_plan(actions: list[dict], label: str, scanned: int | None = None, editing: bool = False) -> str:
    """Текст плана для владелицы: что бот хочет сделать в календаре. Нумерация сквозная
    (в порядке create → rename → delete), по ней владелица может ссылаться в правках."""
    tz = ZoneInfo(config.MARINATWIN_TIMEZONE)
    head = f"\U0001f4cb План для календаря, период «{label}»"
    if scanned is not None:
        head += f" (проверено задач ClickUp: {scanned})"
    head += ". Пока НИЧЕГО не опубликовано."
    if editing:
        head = "✏️ Обновила план. " + head
    lines = [head]
    n = 0
    creates = [a for a in actions if a["type"] == "create"]
    renames = [a for a in actions if a["type"] == "rename"]
    deletes = [a for a in actions if a["type"] == "delete"]
    if creates:
        lines.append(f"\n➕ Добавить в календарь ({len(creates)}):")
        for a in creates:
            n += 1
            try:
                st = datetime.fromisoformat(a["start"]).astimezone(tz)
                en = datetime.fromisoformat(a["end"]).astimezone(tz)
                when = f"{st.strftime('%d.%m %H:%M')}–{en.strftime('%H:%M')}"
            except ValueError:
                when = a["start"]
            loc = f" \U0001f4cd{a['location']}" if a.get("location") else ""
            warn = ""
            if a.get("ambiguous_count"):
                warn = f" ⚠️ рядом уже {a['ambiguous_count']} событий на это время, старые не трогаю"
            lines.append(f"{n}. «{a['title']}» — {when}{loc}{warn}")
    if renames:
        lines.append(f"\n✏️ Переименовать в календаре ({len(renames)}):")
        for a in renames:
            n += 1
            lines.append(f"{n}. «{a['old_title']}» → «{a['new_title']}» — {a.get('when', '')}")
    if deletes:
        lines.append(f"\n\U0001f5d1 Удалить точные дубли ({len(deletes)}):")
        for a in deletes:
            n += 1
            lines.append(f"{n}. «{a['title']}» — {a.get('when', '')} (лишняя копия)")
    lines.append("\nОпубликовать это в календаре?")
    return "\n".join(lines)
