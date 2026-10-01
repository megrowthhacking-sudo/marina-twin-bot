"""
Auto-scheduling ClickUp-задач как встреч в Google Calendar — по прямой просьбе владелицы
(23.09.2026). Обратное направление относительно meeting_extractor.extract_meeting /
bot.py::_propose_meeting_draft (там источник — личное сообщение владелицы, событие
создаётся только после подтверждения кнопкой "✅ Применить"): здесь источник — НОВАЯ
задача в ClickUp workspace, НАЗНАЧЕННАЯ НА ВЛАДЕЛИЦУ (см.
config.CLICKUP_MEETING_WATCH_ASSIGNEE_ID), не только в 4 официальных проектных списках
(config.CLICKUP_LIST_IDS), а по всему workspace — включая WEEKLY TASKS и любые командные
списки (см. clickup_client.get_open_tasks_team_wide). Если задача похожа на
встречу/созвон/звонок — событие в Google Calendar (m@altyn.one) создаётся СРАЗУ, без
каких-либо кнопок подтверждения; владелице только пост-фактум приходит уведомление, чтобы
она могла поправить встречу, если разбор текста ошибся.

check_new_clickup_meetings_job регистрируется в bot.py::build_application и запускается
раз в config.CLICKUP_MEETING_SCAN_INTERVAL_MINUTES минут — только если одновременно
заданы config.CLICKUP_TEAM_WIDE_ENABLED (токен + team_id), config.GOOGLE_CALENDAR_ENABLED
(сервисный аккаунт + calendar_id) и config.OWNER_USER_ID (кому слать уведомление); если
любое из условий не выполнено — job не регистрируется вовсе (см. bot.py).
"""

import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from telegram.ext import ContextTypes

import calendar_client
import clickup_client
import config
import meeting_extractor
import storage

logger = logging.getLogger(__name__)

# Сколько назад от текущего момента считать задачу "новой" — нужно и для серверного
# фильтра ClickUp (date_created_gt, см. clickup_client.get_open_tasks_team_wide), и для
# клиентской перепроверки на случай, если бы в будущем этот фильтр перестал точно
# отсекать старые задачи. Сутки — с запасом относительно интервала скана (несколько
# минут), чтобы не пропустить задачу даже при недолгом простое бота (например, деплое).
_LOOKBACK_HOURS = 24


def _iso_or_none(unix_seconds: float | None, tz: ZoneInfo) -> str | None:
    if not unix_seconds:
        return None
    try:
        return datetime.fromtimestamp(unix_seconds, tz=tz).isoformat()
    except (OverflowError, OSError, ValueError):
        return None


async def _notify_owner(context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    if config.OWNER_USER_ID is None:
        return
    try:
        await context.bot.send_message(chat_id=config.OWNER_USER_ID, text=text)
    except Exception:
        logger.exception("Не удалось отправить пост-фактум уведомление о ClickUp-встрече")


def _collect_weekly_board_candidates(now: datetime) -> tuple[list[dict], dict[str, date]]:
    """Третий источник кандидатов во встречи (добавлен 01.10.2026): доска WEEKLY TASKS
    (config.CLICKUP_LIST_WEEKLY), просканированная по СТАТУСУ-ДНЮ НЕДЕЛИ.

    Зачем это нужно. Жалоба владелицы «0 встреч в календаре»: большинство её
    повторяющихся встреч живёт карточками именно на доске WEEKLY TASKS, где (1) статус
    карточки — название дня недели (например «пятница»), а не due_date, (2) время
    написано прямо в названии карточки (например «11:00 Тетра зум») и (3) поле due_date
    в ClickUp вообще не заполнено. Два прежних запроса (по date_created и по due_date)
    таких карточек принципиально не видят — отсюда «0 встреч».

    Почему ровно 7 дней. Доска — это один полный недельный цикл: каждый из семи
    статусов-дней встречается ровно один раз, поэтому, пройдя дни от сегодняшнего и
    дальше на 7 дней вперёд, мы покрываем всю доску и каждой карточке однозначно
    сопоставляем БЛИЖАЙШУЮ календарную дату её дня недели (сегодняшний статус — на
    сегодня, «завтрашний» — на завтра и т.д.). Это же окно совпадает с окном очистки
    дедупа в storage.cleanup_old_seen_clickup_meeting_tasks (7 суток): запись о том, что
    карточка уже разобрана, живёт неделю и затем удаляется — как раз к моменту, когда
    доска делает полный круг и та же карточка снова становится актуальной на следующей
    неделе, поэтому повторяющаяся встреча ставится в календарь заново каждую неделю, а
    в течение одной недели не дублируется.

    Фильтрация по ответственной (config.CLICKUP_MEETING_WATCH_ASSIGNEE_ID) выполняется на
    стороне ClickUp API. Возвращает (список задач, {task_id: календарная дата дня
    недели}); если config.CLICKUP_WEEKLY_ENABLED выключен — пустые список и словарь.
    Ошибка запроса по одному дню только логируется и не мешает остальным дням."""
    if not config.CLICKUP_WEEKLY_ENABLED:
        return [], {}

    weekday_statuses = [
        config.CLICKUP_WEEKLY_STATUS_COMMANDS[key]["status"]
        for key in ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
    ]

    tasks: list[dict] = []
    target_date_by_task_id: dict[str, date] = {}
    today = now.date()
    for offset in range(7):
        target_date = today + timedelta(days=offset)
        status = weekday_statuses[target_date.weekday()]
        try:
            day_tasks = clickup_client.get_open_tasks(
                config.CLICKUP_LIST_WEEKLY,
                assignee_id=config.CLICKUP_MEETING_WATCH_ASSIGNEE_ID,
                statuses=[status],
            )
        except Exception:
            logger.exception(
                "Не удалось получить карточки WEEKLY TASKS со статусом «%s» для сканирования встреч", status,
            )
            continue
        for task in day_tasks:
            task_id = task.get("id")
            if not task_id or task_id in target_date_by_task_id:
                continue
            target_date_by_task_id[task_id] = target_date
            tasks.append(task)
    return tasks, target_date_by_task_id


def _format_notification(meeting: dict, task_name: str, task_url: str | None, tz: ZoneInfo) -> str:
    start_dt = datetime.fromisoformat(meeting["start"]).astimezone(tz)
    when = start_dt.strftime("%d.%m %H:%M")
    lines = [
        "📅 Автоматически поставила встречу из ClickUp-задачи:",
        f"«{meeting['title']}» — {when}",
    ]
    if meeting.get("location"):
        lines.append(f"📍 {meeting['location']}")
    if meeting.get("time_is_guessed"):
        lines.append("⚠️ Точное время в задаче не нашла — угадала (проверь, пожалуйста).")
    lines.append(f"Задача ClickUp: «{task_name}»" + (f"\n{task_url}" if task_url else ""))
    lines.append("Если это не встреча или что-то не так — поправь событие в календаре вручную.")
    return "\n".join(lines)


async def scan_and_schedule_clickup_meetings(
    context: ContextTypes.DEFAULT_TYPE,
    space_ids: list[str] | None = config.CLICKUP_MEETING_WATCH_SPACE_IDS,
) -> dict:
    """Общая логика скана для фонового job'а (check_new_clickup_meetings_job) и команды
    /calendarclick (bot.py::handle_calendarclick_command). Возвращает статистику:
    {"scanned": int, "created": [{"title", "when", "task_name"}, ...], "errors": int} —
    scanned: сколько ещё не виденных задач разобрано, created: успешно поставленные
    встречи (when — вида "01.10 14:30"), errors: сколько задач не удалось обработать.
    Проверки конфигурации остаются на вызывающей стороне.

    Сканирует пространства ClickUp
    config.CLICKUP_MEETING_WATCH_SPACE_IDS ("РАСПИСАНИЕ" и "ATLAS" — не весь workspace, см.
    докстринг модуля выше) на предмет задач, НАЗНАЧЕННЫХ НА ВЛАДЕЛИЦУ
    (config.CLICKUP_MEETING_WATCH_ASSIGNEE_ID — серверная фильтрация ClickUp API, та же,
    что и у команд по сотрудникам), ТРЕМЯ независимыми источниками кандидатов: (1) созданные
    за последние сутки (ловит вновь заведённые задачи быстро), (2) с due_date в ближайшие
    config.CLICKUP_MEETING_DUE_LOOKAHEAD_DAYS дней (ловит задачи, заведённые заранее кем-то
    другим, но с приближающимся сроком — см. докстринг модуля выше про инцидент с Clear
    Junction) и (3) добавлено 01.10.2026 — скан доски WEEKLY TASKS по статусу-дню недели
    (см. _collect_weekly_board_candidates): повторяющиеся встречи там заведены карточками
    со статусом «пятница» и т.п., временем прямо в названии и БЕЗ due_date, поэтому
    первые два запроса их не видят (жалоба «0 встреч в календаре»). Результаты
    объединяются по id задачи. Для каждой ещё не виденной задачи (см.
    storage.has_seen_clickup_meeting_task) прогоняет её полный текст (название + описание)
    через meeting_extractor.extract_meeting_from_task. Если задача похожа на
    встречу/созвон/звонок — сразу создаёт событие в Google Calendar (без подтверждения) и
    шлёт владелице пост-фактум уведомление. Любая ошибка на отдельной задаче только
    логируется — не должна останавливать обработку остальных задач этого скана."""
    stats: dict = {"scanned": 0, "created": [], "errors": 0}

    tz = ZoneInfo(config.MARINATWIN_TIMEZONE)
    now = datetime.now(tz)
    cutoff = now - timedelta(hours=_LOOKBACK_HOURS)
    cutoff_ms = int(cutoff.timestamp() * 1000)

    try:
        new_tasks = clickup_client.get_open_tasks_team_wide(
            assignee_id=config.CLICKUP_MEETING_WATCH_ASSIGNEE_ID,
            date_created_gt_ms=cutoff_ms,
            space_ids=space_ids,
        )
    except Exception:
        logger.exception("Не удалось получить новые задачи ClickUp для сканирования встреч")
        new_tasks = []

    due_from_ms = int(now.timestamp() * 1000)
    due_to_ms = int((now + timedelta(days=config.CLICKUP_MEETING_DUE_LOOKAHEAD_DAYS)).timestamp() * 1000)
    try:
        due_soon_tasks = clickup_client.get_open_tasks_team_wide(
            assignee_id=config.CLICKUP_MEETING_WATCH_ASSIGNEE_ID,
            due_date_gt_ms=due_from_ms,
            due_date_lt_ms=due_to_ms,
            space_ids=space_ids,
        )
    except Exception:
        logger.exception("Не удалось получить задачи ClickUp с приближающимся due_date для сканирования встреч")
        due_soon_tasks = []

    weekly_board_tasks, weekly_target_date_by_task_id = _collect_weekly_board_candidates(now)

    if not new_tasks and not due_soon_tasks and not weekly_board_tasks:
        return stats

    # Для due_soon и карточек WEEKLY TASKS проверка устаревшего date_created не нужна:
    # они могли быть заведены давно, но всё равно актуальны на ближайшие дни.
    skip_staleness_check_ids = {task.get("id") for task in due_soon_tasks if task.get("id")}
    skip_staleness_check_ids |= {task.get("id") for task in weekly_board_tasks if task.get("id")}
    tasks_by_id: dict[str, dict] = {}
    for task in new_tasks + due_soon_tasks + weekly_board_tasks:
        task_id = task.get("id")
        if task_id:
            tasks_by_id.setdefault(task_id, task)
    tasks = list(tasks_by_id.values())

    for task in tasks:
        task_id = task.get("id")
        if not task_id:
            continue
        if task_id not in skip_staleness_check_ids:
            created = task.get("date_created") or 0
            if created and created < cutoff.timestamp():
                continue
        if storage.has_seen_clickup_meeting_task(task_id):
            continue

        stats["scanned"] += 1
        try:
            full_task = clickup_client.get_task(task_id)
        except Exception:
            logger.exception("Не удалось прочитать полную задачу ClickUp %s для анализа встречи", task_id)
            stats["errors"] += 1
            continue
        if not full_task:
            storage.mark_seen_clickup_meeting_task(task_id)
            continue

        description = full_task.get("description") or ""
        due_iso = _iso_or_none(task.get("due_date"), tz)
        created_iso = _iso_or_none(task.get("date_created"), tz)

        weekday_target_date = weekly_target_date_by_task_id.get(task_id)
        weekday_hint_date_iso = f"{weekday_target_date.isoformat()}T00:00:00" if weekday_target_date else None

        try:
            meeting = meeting_extractor.extract_meeting_from_task(
                title=task.get("name") or full_task.get("name") or "(без названия)",
                description=description,
                due_date_iso=due_iso,
                created_iso=created_iso,
                tz_name=config.MARINATWIN_TIMEZONE,
                weekday_hint_date_iso=weekday_hint_date_iso,
            )
        except Exception:
            logger.exception("Ошибка при разборе задачи ClickUp %s на предмет встречи", task_id)
            storage.mark_seen_clickup_meeting_task(task_id)
            stats["errors"] += 1
            continue

        if not meeting:
            storage.mark_seen_clickup_meeting_task(task_id)
            continue

        try:
            calendar_client.create_event(
                meeting["title"],
                meeting["start"],
                meeting["end"],
                location=meeting.get("location") or None,
                description=f"Авто-поставлено из ClickUp-задачи: {task.get('url') or task_id}",
            )
        except Exception:
            logger.exception(
                "Не удалось создать событие Google Calendar из ClickUp-задачи %s («%s»)",
                task_id, task.get("name"),
            )
            stats["errors"] += 1
            continue

        storage.mark_seen_clickup_meeting_task(task_id)
        task_name = task.get("name") or "(без названия)"
        try:
            when = datetime.fromisoformat(meeting["start"]).astimezone(tz).strftime("%d.%m %H:%M")
        except (ValueError, TypeError):
            when = str(meeting.get("start") or "")
        stats["created"].append({"title": meeting["title"], "when": when, "task_name": task_name})
        await _notify_owner(context, _format_notification(meeting, task_name, task.get("url"), tz))

    storage.cleanup_old_seen_clickup_meeting_tasks()
    return stats


async def check_new_clickup_meetings_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Фоновый job (раз в config.CLICKUP_MEETING_SCAN_INTERVAL_MINUTES): проверяет
    конфигурацию и делегирует скан в scan_and_schedule_clickup_meetings (у которого с
    01.10.2026 есть третий источник кандидатов — скан доски WEEKLY TASKS по статусу-дню
    недели, см. _collect_weekly_board_candidates). Статистика не нужна — это фон,
    обратной связи нет."""
    if not (config.CLICKUP_TEAM_WIDE_ENABLED and config.GOOGLE_CALENDAR_ENABLED and config.OWNER_USER_ID):
        return
    await scan_and_schedule_clickup_meetings(context)
