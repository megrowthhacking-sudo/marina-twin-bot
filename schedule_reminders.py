"""
Точечные напоминания и утренний план на день — по прямому запросу владелицы, часть 42.
Три источника расписания: Google Calendar (calendar_client) — все встречи; ClickUp
WEEKLY TASKS (clickup_client) — задачи со статусом текущего дня недели и заданным
due_date; Trello (trello_client) — карточки колонки текущего дня недели, требует
отдельных credentials, неактивен пока config.TRELLO_ENABLED == False.
Регистрируется в bot.py::build_application: check_and_send_reminders_job (раз в
config.REMINDER_CHECK_INTERVAL_MINUTES минут) и morning_plan_job (раз в день).
"""
import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram.error import RetryAfter
from telegram.ext import ContextTypes
import calendar_client
import clickup_client
import config
import storage
import trello_client

logger = logging.getLogger(__name__)
_SOURCE_ICONS = {"calendar": "📅", "clickup": "🗂", "trello": "📋"}

def _now() -> datetime:
 return datetime.now(ZoneInfo(config.MARINATWIN_TIMEZONE))

async def _send_to_owner(context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
 if config.OWNER_USER_ID is None:
 return False
 try:
 await context.bot.send_message(chat_id=config.OWNER_USER_ID, text=text)
 return True
 except RetryAfter as e:
 try:
 await asyncio.sleep(e.retry_after + 0.1)
 await context.bot.send_message(chat_id=config.OWNER_USER_ID, text=text)
 return True
 except Exception:
 logger.exception("Не удалось отправить напоминание о расписании владелице (после повтора)")
 return False
 except Exception:
 logger.exception("Не удалось отправить напоминание о расписании владелице")
 return False

def _today_weekday_status_label() -> str | None:
 if not config.CLICKUP_WEEKLY_ENABLED:
 return None
 key = config.SCHEDULE_WEEKDAY_STATUS_KEYS[_now().weekday()]
 return config.CLICKUP_WEEKLY_STATUS_COMMANDS[key]["status"]

def _collect_timed_items(now: datetime, window_end: datetime) -> list[dict]:
 items: list[dict] = []
 if config.GOOGLE_CALENDAR_ENABLED:
 try:
 events = calendar_client.list_events(now.isoformat(), window_end.isoformat())
 except Exception:
 logger.exception("Не удалось получить события Google Calendar для напоминаний")
 events = []
 for event in events:
 if event.get("all_day"):
 continue
 try:
 when = datetime.fromisoformat(event["start"])
 except (ValueError, TypeError):
 continue
 items.append(
 {
 "source": "calendar",
 "item_id": f"{event['start']}:{event['title']}",
 "title": event["title"],
 "when": when,
 "url": None,
 }
 )
 status_label = _today_weekday_status_label()
 if status_label is not None:
 try:
 tasks = clickup_client.get_open_tasks(config.CLICKUP_LIST_WEEKLY, statuses=[status_label])
 except Exception:
 logger.exception("Не удалось получить задачи WEEKLY TASKS для напоминаний")
 tasks = []
 for task in tasks:
 due = task.get("due_date")
 if not due:
 continue
 when = datetime.fromtimestamp(due, tz=ZoneInfo(config.MARINATWIN_TIMEZONE))
 items.append(
 {"source": "clickup", "item_id": task["id"], "title": task["name"], "when": when, "url": task.get("url")}
 )
 if config.TRELLO_ENABLED:
 weekday_name = config.SCHEDULE_WEEKDAY_NAMES[now.weekday()]
 try:
 cards = trello_client.get_weekday_cards(weekday_name)
 except Exception:
 logger.exception("Не удалось получить карточки Trello для напоминаний")
 cards = []
 for card in cards:
 due = card.get("due")
 if not due:
 continue
 try:
 when = datetime.fromisoformat(due.replace("Z", "+00:00"))
 except (ValueError, AttributeError):
 continue
 items.append(
 {"source": "trello", "item_id": card["id"], "title": card["name"], "when": when, "url": card.get("url")}
 )
 return [item for item in items if now <= item["when"] < window_end]

async def check_and_send_reminders_job(context: ContextTypes.DEFAULT_TYPE) -> None:
 if not config.SCHEDULE_REMINDERS_ENABLED:
 return
 now = _now()
 max_lead = max(config.REMINDER_LEAD_MINUTES)
 window_end = now + timedelta(minutes=max_lead + config.REMINDER_CHECK_INTERVAL_MINUTES)
 items = _collect_timed_items(now, window_end)
 for item in items:
 minutes_until = (item["when"] - now).total_seconds() / 60
 for lead in config.REMINDER_LEAD_MINUTES:
 if not (lead - config.REMINDER_CHECK_INTERVAL_MINUTES < minutes_until <= lead):
 continue
 reminder_key = f"{item['source']}:{item['item_id']}:{lead}"
 if storage.has_sent_reminder(reminder_key):
 continue
 icon = _SOURCE_ICONS.get(item["source"], "🔔")
 when_str = item["when"].astimezone(ZoneInfo(config.MARINATWIN_TIMEZONE)).strftime("%H:%M")
 text = f"{icon} Марина, через {lead} мин ({when_str}) — «{item['title']}»"
 if item.get("url"):
 text += f"\n{item['url']}"
 if await _send_to_owner(context, text):
 storage.mark_reminder_sent(reminder_key)
 storage.cleanup_old_sent_reminders()

def _format_plan_line(item: dict) -> str:
 when_str = item["when"].astimezone(ZoneInfo(config.MARINATWIN_TIMEZONE)).strftime("%H:%M")
 icon = _SOURCE_ICONS.get(item["source"], "🔔")
 return f"{icon} {when_str} — {item['title']}"

async def morning_plan_job(context: ContextTypes.DEFAULT_TYPE) -> None:
 if not config.SCHEDULE_REMINDERS_ENABLED:
 return
 now = _now()
 day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
 day_end = day_start + timedelta(days=1)
 timed_items: list[dict] = []
 untimed_lines: list[str] = []
 if config.GOOGLE_CALENDAR_ENABLED:
 try:
 events = calendar_client.list_events(day_start.isoformat(), day_end.isoformat())
 except Exception:
 logger.exception("Не удалось получить события Google Calendar для плана на день")
 events = []
 for event in events:
 if event.get("all_day"):
 untimed_lines.append(f"📅 {event['title']} (весь день)")
 continue
 try:
 when = datetime.fromisoformat(event["start"])
 except (ValueError, TypeError):
 continue
 timed_items.append({"source": "calendar", "title": event["title"], "when": when})
 status_label = _today_weekday_status_label()
 if status_label is not None:
 try:
 tasks = clickup_client.get_open_tasks(config.CLICKUP_LIST_WEEKLY, statuses=[status_label])
 except Exception:
 logger.exception("Не удалось получить задачи WEEKLY TASKS для плана на день")
 tasks = []
 for task in tasks:
 due = task.get("due_date")
 if due:
 when = datetime.fromtimestamp(due, tz=ZoneInfo(config.MARINATWIN_TIMEZONE))
 timed_items.append({"source": "clickup", "title": task["name"], "when": when})
 else:
 untimed_lines.append(f"🗂 {task['name']}")
 if config.TRELLO_ENABLED:
 weekday_name = config.SCHEDULE_WEEKDAY_NAMES[now.weekday()]
 try:
 cards = trello_client.get_weekday_cards(weekday_name)
 except Exception:
 logger.exception("Не удалось получить карточки Trello для плана на день")
 cards = []
 for card in cards:
 due = card.get("due")
 when = None
 if due:
 try:
 when = datetime.fromisoformat(due.replace("Z", "+00:00"))
 except (ValueError, AttributeError):
 when = None
 if when is not None:
 timed_items.append({"source": "trello", "title": card["name"], "when": when})
 else:
 untimed_lines.append(f"📋 {card['name']}")
 if not timed_items and not untimed_lines:
 return
 timed_items.sort(key=lambda i: i["when"])
 lines = [_format_plan_line(i) for i in timed_items] + untimed_lines
 weekday_label = config.SCHEDULE_WEEKDAY_NAMES[now.weekday()].capitalize()
 header = f"☀️ План на сегодня, {now.strftime('%d.%m')} ({weekday_label}):"
 text = header + "\n\n" + "\n".join(lines)
 await _send_to_owner(context, text)
