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

import json
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


def _is_owner_task(task: dict) -> bool:
    """Клиентский фильтр по ответственной (03.10.2026). True, если у карточки НЕТ
    назначенных (собственные карточки-встречи владелицы почти всегда без исполнителя) ИЛИ
    среди назначенных есть сама владелица (имя из ClickUp сопоставляется через
    config.CLICKUP_ASSIGNEE_MAP с config.CLICKUP_MEETING_WATCH_ASSIGNEE_ID). Карточки,
    назначенные только на кого-то ещё, отбрасываются."""
    assignees = task.get("assignees") or []
    if not assignees:
        return True
    return any(
        config.CLICKUP_ASSIGNEE_MAP.get(name.lower()) == config.CLICKUP_MEETING_WATCH_ASSIGNEE_ID
        for name in assignees
    )


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

    Фильтр по ответственной — клиентский, не через ClickUp API (изменено 01.10.2026,
    дважды). Сначала фильтр assignee_id=config.CLICKUP_MEETING_WATCH_ASSIGNEE_ID вообще
    убрали на стороне ClickUp API-запроса: собственные карточки-встречи владелицы на этой
    доске вида «11:00 собес юрист BS» почти всегда БЕЗ назначенного исполнителя в ClickUp
    (assignees: []), и такой фильтр их отсеивал целиком. Но без какого-либо фильтра стали
    проскакивать обычные задачи ДРУГИХ сотрудников, которые просто тоже лежат в
    статусах-днях недели этой доски (это общий kanban этой доски, не только её личное
    расписание) — например задача, назначенная только на Юрия, иногда звучит достаточно
    похоже на созвон, чтобы meeting_extractor её пропустил, хотя это не встреча владелицы.
    Поэтому ниже оставляем карточку кандидатом, только если у неё НЕТ назначенных (так
    устроены её собственные карточки-встречи) ИЛИ среди назначенных есть она сама
    (сравнение имени из ClickUp через config.CLICKUP_ASSIGNEE_MAP) — карточки, назначенные
    только на кого-то ещё, отбрасываются сразу, до вызова meeting_extractor.
    Возвращает (список задач, {task_id: календарная дата дня недели}); если
    config.CLICKUP_WEEKLY_ENABLED выключен — пустые список и словарь. Ошибка запроса по
    одному дню только логируется и не мешает остальным дням."""
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
            if not _is_owner_task(task):
                continue
            target_date_by_task_id[task_id] = target_date
            tasks.append(task)
    return tasks, target_date_by_task_id


def _collect_period_meeting_candidates(
    start: datetime, end: datetime, now: datetime,
) -> tuple[list[dict], dict[str, date]]:
    """Общий сбор кандидатов-задач ClickUp за период [start, end) — используется
    reconcile_clickup_titles_in_calendar (см. ниже — единая команда /calendarclickup, по
    прямой просьбе владелицы: сверить её встречи ClickUp с уже стоящими в календаре,
    переименовать те, что названы по-другому, доставить отсутствующие и убрать точные
    дубли; до 02.10.2026 было две отдельные команды — /calendarclick и /calendarclickup —
    объединены в одну по прямой просьбе владелицы, слишком похожи и путали). Источники:
    (1) due_date внутри периода, (2) доска WEEKLY TASKS по дню недели в периоде,
    (3) любая задача workspace с явной датой в названии, попадающей в период. Источники (1)
    и (3) фильтруются по ответственной на клиенте через _is_owner_task (с 03.10.2026, а не
    серверным assignee_id): карточки владелицы без назначенного исполнителя вне доски
    WEEKLY TASKS раньше отсекались серверным фильтром. Возвращает
    (объединённый по id список сырых задач ClickUp, {task_id: дата дня недели с доски
    WEEKLY TASKS}) — второе нужно вызывающему коду для weekday_hint_date_iso при вызове
    meeting_extractor.extract_meeting_from_task."""
    try:
        due_tasks_raw = clickup_client.get_open_tasks_team_wide(
            due_date_gt_ms=int(start.timestamp() * 1000),
            due_date_lt_ms=int(end.timestamp() * 1000),
            space_ids=None,
        )
    except Exception:
        logger.exception("Не удалось получить задачи ClickUp с due_date в периоде")
        due_tasks_raw = []
    due_tasks = [task for task in due_tasks_raw if _is_owner_task(task)]
    weekly_board_tasks, weekly_target_date_by_task_id = _collect_weekly_board_candidates(now)
    start_date = start.date()
    end_date = end.date()
    weekly_board_tasks = [
        task
        for task in weekly_board_tasks
        if start_date <= weekly_target_date_by_task_id.get(task.get("id"), start_date - timedelta(days=1)) < end_date
    ]
    try:
        all_tasks_raw = clickup_client.get_open_tasks_team_wide(
            space_ids=None,
        )
    except Exception:
        logger.exception("Не удалось получить все задачи ClickUp владелицы за период")
        all_tasks_raw = []
    all_own_tasks = [task for task in all_tasks_raw if _is_owner_task(task)]
    explicit_date_tasks = []
    for task in all_own_tasks:
        name = task.get("name") or ""
        explicit_match = meeting_extractor.parse_explicit_date_time(name, now)
        if explicit_match and start_date <= explicit_match["start"].date() < end_date:
            explicit_date_tasks.append(task)
    tasks_by_id: dict[str, dict] = {}
    for task in due_tasks + weekly_board_tasks + explicit_date_tasks:
        task_id = task.get("id")
        if task_id:
            tasks_by_id.setdefault(task_id, task)
    return list(tasks_by_id.values()), weekly_target_date_by_task_id


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
    """Общая логика скана для фонового job'а (check_new_clickup_meetings_job) — раньше
    её же вызывала и команда /calendarclick, пока та сама сразу сканировала только
    новые задачи; с 01.10.2026 /calendarclick переключилась на
    ensure_period_clickup_meetings_in_calendar (полный обзор периода), а с 02.10.2026
    обе отдельные команды /calendarclick и /calendarclickup объединены в одну — см.
    reconcile_clickup_titles_in_calendar. Эта функция теперь используется только фоном.
    Возвращает статистику:
    {"scanned": int, "created": [{"title", "when", "task_name"}, ...], "errors": int} —
    scanned: сколько ещё не виденных задач разобрано, created: успешно поставленные
    встречи (when — вида "01.10 14:30"), errors: сколько задач не удалось обработать.
    Проверки конфигурации остаются на вызывающей стороне.

    Сканирует пространства ClickUp
    config.CLICKUP_MEETING_WATCH_SPACE_IDS ("РАСПИСАНИЕ" и "ATLAS" — не весь workspace, см.
    докстринг модуля выше) на предмет задач ВЛАДЕЛИЦЫ ИЛИ БЕЗ НАЗНАЧЕННОГО ИСПОЛНИТЕЛЯ
    (config.CLICKUP_MEETING_WATCH_ASSIGNEE_ID). Фильтр по ответственной перенесён с
    сервера ClickUp на клиент (_is_owner_task, 03.10.2026): серверный assignee_id отсекал
    собственные карточки владелицы без исполнителя вне доски WEEKLY TASKS — жалоба
    владелицы 03.10.2026 «не тянет корректно все мои зумы и встречи». Теперь карточки,
    назначенные только на других, по-прежнему отбрасываются, а неназначенные —
    попадают в кандидаты. ТРЕМЯ независимыми источниками кандидатов: (1) созданные
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
        new_tasks_raw = clickup_client.get_open_tasks_team_wide(
            date_created_gt_ms=cutoff_ms,
            space_ids=space_ids,
        )
    except Exception:
        logger.exception("Не удалось получить новые задачи ClickUp для сканирования встреч")
        new_tasks_raw = []
    new_tasks = [task for task in new_tasks_raw if _is_owner_task(task)]

    due_from_ms = int(now.timestamp() * 1000)
    due_to_ms = int((now + timedelta(days=config.CLICKUP_MEETING_DUE_LOOKAHEAD_DAYS)).timestamp() * 1000)
    try:
        due_soon_tasks_raw = clickup_client.get_open_tasks_team_wide(
            due_date_gt_ms=due_from_ms,
            due_date_lt_ms=due_to_ms,
            space_ids=space_ids,
        )
    except Exception:
        logger.exception("Не удалось получить задачи ClickUp с приближающимся due_date для сканирования встреч")
        due_soon_tasks_raw = []
    due_soon_tasks = [task for task in due_soon_tasks_raw if _is_owner_task(task)]

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
    обратной связи нет.
    space_ids=None (01.10.2026, по прямой просьбе владелицы) — скан, как и у
    /calendarclickup, идёт по ВСЕМУ workspace, а не только по config.CLICKUP_MEETING_WATCH_SPACE_IDS
    (РАСПИСАНИЕ + ATLAS). Раньше фон был уже сужен специально, чтобы не захламлять
    календарь встречами коллег (24.09.2026) — это сознательно отменено по новой просьбе
    владелицы: теперь любая похожая на встречу задача, назначенная на неё, из любого
    пространства, авто-ставится в календарь."""
    if not (config.CLICKUP_TEAM_WIDE_ENABLED and config.GOOGLE_CALENDAR_ENABLED and config.OWNER_USER_ID):
        return
    await scan_and_schedule_clickup_meetings(context, space_ids=None)


def _fmt_when(iso: str, tz: ZoneInfo) -> str:
    try:
        return datetime.fromisoformat(iso).astimezone(tz).strftime("%d.%m %H:%M")
    except (ValueError, TypeError):
        return iso or ""


async def plan_clickup_calendar_sync(start: datetime, end: datetime) -> dict:
    """ТОЛЬКО ЧИТАЕТ (ничего не пишет ни в календарь, ни в storage): готовит план сверки
    ClickUp-встреч за период [start, end) с личным календарём (m@altyn.one) для команды
    /calendarclickup (03.10.2026, по прямой просьбе владелицы: бот сначала присылает план
    в личку с кнопками "Опубликовать/Изменить/Отмена" и пишет в календарь только после
    "Опубликовать" — см. bot.py и apply_calendar_actions ниже).
    Логика сопоставления та же, что была у прямой сверки: по ВРЕМЕНИ, а не по названию
    (окно ±30 минут вокруг встречи). Ни одного события рядом — действие "create"; ровно
    одно с другим названием — "rename"; несколько — "create" с ambiguous_count (событие
    добавляется, старые не трогаем, владелица видит предупреждение). Уже запланированные
    "create" этого же плана на ТО ЖЕ САМОЕ время учитываются как виртуальные события — иначе две задачи
    ClickUp на одно время дали бы два одинаковых create.
    Возвращает {"scanned", "actions": [...], "unchanged", "ambiguous_skipped": [...],
    "errors"}. Действия — JSON-совместимые dict:
    {"type": "create", "title", "start", "end", "location", "description", "task_id",
    "ambiguous_count"}; {"type": "rename", "event_id", "old_title", "new_title", "when"}."""
    plan: dict = {"scanned": 0, "actions": [], "unchanged": 0, "ambiguous_skipped": [], "errors": 0}
    tz = ZoneInfo(config.MARINATWIN_TIMEZONE)
    now = datetime.now(tz)
    tasks, weekly_target_date_by_task_id = _collect_period_meeting_candidates(start, end, now)
    virtual: list[dict] = []
    for task in tasks:
        task_id = task.get("id")
        if not task_id:
            continue
        plan["scanned"] += 1
        try:
            full_task = clickup_client.get_task(task_id)
        except Exception:
            logger.exception("Не удалось прочитать задачу ClickUp %s для /calendarclickup", task_id)
            plan["errors"] += 1
            continue
        if not full_task:
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
            logger.exception("Ошибка разбора задачи ClickUp %s для /calendarclickup", task_id)
            plan["errors"] += 1
            continue
        if not meeting:
            continue
        try:
            meeting_start = datetime.fromisoformat(meeting["start"]).astimezone(tz)
            meeting_end = datetime.fromisoformat(meeting["end"]).astimezone(tz)
        except (ValueError, KeyError, TypeError):
            continue
        if not (start <= meeting_start < end):
            continue
        win_start = meeting_start - timedelta(minutes=30)
        win_end = meeting_end + timedelta(minutes=30)
        try:
            nearby = calendar_client.list_events(win_start.isoformat(), win_end.isoformat())
        except Exception:
            logger.exception("Не удалось прочитать календарь рядом с %s для /calendarclickup", meeting_start)
            plan["errors"] += 1
            continue
        nearby = [e for e in nearby if not e.get("all_day")]
        for v in virtual:
            try:
                v_start = datetime.fromisoformat(v["start"])
                v_end = datetime.fromisoformat(v["end"])
            except ValueError:
                continue
            if v_start == meeting_start and v_end == meeting_end:
                nearby.append({"id": None, "title": v["title"], "start": v["start"], "end": v["end"]})
        when = meeting_start.strftime("%d.%m %H:%M")
        task_url = task.get("url") or task_id
        create_action = {
            "type": "create",
            "title": meeting["title"],
            "start": meeting["start"],
            "end": meeting["end"],
            "location": meeting.get("location") or None,
            "description": f"Авто-поставлено из ClickUp-задачи: {task_url}",
            "task_id": task_id,
            "ambiguous_count": None,
        }
        if not nearby:
            plan["actions"].append(create_action)
            virtual.append({"title": meeting["title"], "start": meeting["start"], "end": meeting["end"]})
            continue
        if len(nearby) > 1:
            create_action["ambiguous_count"] = len(nearby)
            plan["actions"].append(create_action)
            virtual.append({"title": meeting["title"], "start": meeting["start"], "end": meeting["end"]})
            continue
        existing = nearby[0]
        if existing.get("title", "").strip().lower() == meeting["title"].strip().lower():
            plan["unchanged"] += 1
            continue
        event_id = existing.get("id")
        if not event_id:
            plan["ambiguous_skipped"].append({"title": meeting["title"], "when": when, "count": 1})
            continue
        plan["actions"].append(
            {
                "type": "rename",
                "event_id": event_id,
                "old_title": existing.get("title", ""),
                "new_title": meeting["title"],
                "when": when,
            }
        )
    return plan


async def plan_calendar_dedupe(start: datetime, end: datetime) -> dict:
    """ТОЛЬКО ЧИТАЕТ: ищет в личном календаре ТОЧНЫЕ дубли за период [start, end) и
    возвращает действия "delete" для лишних копий (одну копию в каждой группе оставляет).
    "Точный дубль" — намеренно строгое определение (по прямой просьбе владелицы, чтобы не
    снести две разные встречи, которые просто совпали по времени): ОДНО И ТО ЖЕ название
    (без учёта регистра и пробелов по краям) И ОДНО И ТО ЖЕ время начала/конца. Событие с
    другим названием в то же время дублем НЕ считается. all_day события не участвуют.
    Внутри группы остаётся первое событие (порядок Google Calendar — по startTime).
    Возвращает {"scanned", "actions": [{"type": "delete", "event_id", "title", "when"}],
    "errors"}."""
    plan: dict = {"scanned": 0, "actions": [], "errors": 0}
    tz = ZoneInfo(config.MARINATWIN_TIMEZONE)
    try:
        events = calendar_client.list_events(start.isoformat(), end.isoformat())
    except Exception:
        logger.exception("Не удалось прочитать календарь для поиска дублей (/calendarclickup)")
        plan["errors"] += 1
        return plan
    events = [e for e in events if not e.get("all_day")]
    plan["scanned"] = len(events)
    groups: dict[tuple[str, str, str], list[dict]] = {}
    for e in events:
        key = (e.get("title", "").strip().lower(), e.get("start"), e.get("end"))
        groups.setdefault(key, []).append(e)

    for (_title_key, start_iso, _end_iso), group in groups.items():
        if len(group) < 2:
            continue
        keep, *extra = group
        display_title = keep.get("title") or "(без названия)"
        when = _fmt_when(start_iso, tz)
        for dup in extra:
            event_id = dup.get("id")
            if not event_id:
                continue
            plan["actions"].append(
                {"type": "delete", "event_id": event_id, "title": display_title, "when": when}
            )
    return plan


def apply_calendar_actions(actions: list[dict]) -> dict:
    """Единственное место, где /calendarclickup ПИШЕТ в календарь (после "Опубликовать"
    владелицы): выполняет действия плана по порядку. Ошибка одного действия только
    логируется и не мешает остальным. Для "create" с task_id помечает задачу ClickUp как
    уже обработанную (storage.mark_seen_clickup_meeting_task) — чтобы фоновый автоскан не
    поставил её второй раз.
    Возвращает {"created": [{"title", "when"}], "renamed": [{"old_title", "new_title",
    "when"}], "deleted": [{"title", "when", "removed"}], "ambiguous": [{"title", "when",
    "count"}], "errors": int}."""
    tz = ZoneInfo(config.MARINATWIN_TIMEZONE)
    result: dict = {"created": [], "renamed": [], "deleted": [], "ambiguous": [], "errors": 0}
    deleted_by_key: dict[tuple[str, str], dict] = {}
    for action in actions:
        kind = action.get("type")
        if kind == "create":
            when = _fmt_when(action["start"], tz)
            try:
                calendar_client.create_event(
                    action["title"],
                    action["start"],
                    action["end"],
                    location=action.get("location") or None,
                    description=action.get("description") or None,
                )
            except Exception:
                logger.exception("Не удалось создать событие «%s» (/calendarclickup)", action.get("title"))
                result["errors"] += 1
                continue
            if action.get("task_id"):
                storage.mark_seen_clickup_meeting_task(action["task_id"])
            result["created"].append({"title": action["title"], "when": when})
            if action.get("ambiguous_count"):
                result["ambiguous"].append(
                    {"title": action["title"], "when": when, "count": action["ambiguous_count"]}
                )
        elif kind == "rename":
            try:
                calendar_client.update_event(action["event_id"], title=action["new_title"])
            except Exception:
                logger.exception(
                    "Не удалось переименовать событие %s в «%s» (/calendarclickup)",
                    action.get("event_id"), action.get("new_title"),
                )
                result["errors"] += 1
                continue
            result["renamed"].append(
                {"old_title": action.get("old_title", ""), "new_title": action["new_title"], "when": action.get("when", "")}
            )
        elif kind == "delete":
            try:
                calendar_client.delete_event(action["event_id"])
            except Exception:
                logger.exception("Не удалось удалить дубль «%s» (/calendarclickup)", action.get("title"))
                result["errors"] += 1
                continue
            key = (action.get("title", ""), action.get("when", ""))
            if key in deleted_by_key:
                deleted_by_key[key]["removed"] += 1
            else:
                entry = {"title": key[0], "when": key[1], "removed": 1}
                deleted_by_key[key] = entry
                result["deleted"].append(entry)
    return result


async def reconcile_clickup_titles_in_calendar(start: datetime, end: datetime) -> dict:
    """Прямая сверка без подтверждения (план + сразу применение) — оставлена как обёртка
    для совместимости; команда /calendarclickup с 03.10.2026 использует
    plan_clickup_calendar_sync + кнопки подтверждения + apply_calendar_actions.
    Возвращает {"scanned", "renamed", "created", "unchanged", "ambiguous", "errors"}."""
    plan = await plan_clickup_calendar_sync(start, end)
    applied = apply_calendar_actions(plan["actions"])
    return {
        "scanned": plan["scanned"],
        "renamed": applied["renamed"],
        "created": applied["created"],
        "unchanged": plan["unchanged"],
        "ambiguous": applied["ambiguous"] + plan["ambiguous_skipped"],
        "errors": plan["errors"] + applied["errors"],
    }


async def dedupe_calendar_events(start: datetime, end: datetime) -> dict:
    """Прямая зачистка точных дублей без подтверждения (план + сразу применение) —
    обёртка для совместимости, см. plan_calendar_dedupe. Возвращает {"scanned",
    "deleted": [{"title", "when", "removed"}], "errors"}."""
    plan = await plan_calendar_dedupe(start, end)
    applied = apply_calendar_actions(plan["actions"])
    return {"scanned": plan["scanned"], "deleted": applied["deleted"], "errors": plan["errors"] + applied["errors"]}


_REVISE_SYSTEM_PROMPT = """Ты помогаешь владелице поправить ПЛАН изменений её Google Calendar перед публикацией.
Сейчас {today} ({tz_name}). План — нумерованный список действий (JSON). Владелица прислала правку своими словами.
Типы действий: "create" (добавить встречу: title, start, end, location), "rename" (переименовать событие: new_title), "delete" (удалить точный дубль).
Что можно: убрать действие из плана (не включать его в ответ); изменить title/start/end/location у "create"; изменить new_title у "rename"; добавить новое "create" (ref = null), если она просит добавить встречу.
Что нельзя: менять тип существующего действия, придумывать event_id.
start/end — ISO 8601 с таймзоной {tz_name} (например 2026-10-05T15:00:00+03:00); если конец не указан — start + 1 час. Всё, что владелица не просила менять, оставь как есть.
Если правка непонятна — верни {{"ok": false}}.
Ответ — ТОЛЬКО JSON без пояснений: {{"ok": true, "actions": [{{"ref": <номер из плана или null для нового>, "title": "...", "new_title": "...", "start": "...", "end": "...", "location": "..."}}]}} (поля — только те, что нужны для типа)."""


def revise_calendar_plan(actions: list[dict], user_text: str) -> list[dict] | None:
    """Применяет правку владелицы (свободный текст) к плану /calendarclickup через
    лёгкую модель. Возвращает новый список действий (в порядке create → rename → delete)
    или None, если правку не удалось понять/ответ модели невалиден. Код сам проверяет
    ответ: типы существующих действий и event_id берутся ТОЛЬКО из исходного плана,
    модель их изменить не может; новые действия — только "create" с валидными ISO-датами
    и end > start."""
    from claude_client import client  # локальный импорт: тесты подменяют модуль
    tz = ZoneInfo(config.MARINATWIN_TIMEZONE)
    now = datetime.now(tz)
    listing = []
    for i, a in enumerate(actions, start=1):
        item = {"n": i, "type": a["type"]}
        if a["type"] == "create":
            item.update(title=a["title"], start=a["start"], end=a["end"], location=a.get("location"))
        elif a["type"] == "rename":
            item.update(old_title=a["old_title"], new_title=a["new_title"], when=a.get("when"))
        else:
            item.update(title=a["title"], when=a.get("when"))
        listing.append(item)
    system_prompt = _REVISE_SYSTEM_PROMPT.format(today=now.strftime("%Y-%m-%d %H:%M, %A"), tz_name=config.MARINATWIN_TIMEZONE)
    response = client.messages.create(
        model=config.LIGHT_MODEL_NAME,
        max_tokens=2048,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": "ПЛАН:\n" + json.dumps(listing, ensure_ascii=False) + "\n\nПРАВКА ВЛАДЕЛИЦЫ:\n" + user_text,
            }
        ],
    )
    raw = "\n".join(block.text for block in response.content if block.type == "text").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("revise_calendar_plan: невалидный JSON от модели: %s", raw[:500])
        return None
    if not isinstance(parsed, dict) or not parsed.get("ok") or not isinstance(parsed.get("actions"), list):
        return None
    revised: list[dict] = []
    used_refs: set[int] = set()
    for item in parsed["actions"]:
        if not isinstance(item, dict):
            return None
        ref = item.get("ref")
        if ref is None:
            title = (item.get("title") or "").strip()
            try:
                new_start = datetime.fromisoformat(item.get("start") or "")
                new_end = datetime.fromisoformat(item.get("end") or "")
            except ValueError:
                return None
            if not title or new_start.tzinfo is None or new_end.tzinfo is None or new_end <= new_start:
                return None
            revised.append(
                {
                    "type": "create", "title": title, "start": new_start.isoformat(), "end": new_end.isoformat(),
                    "location": (item.get("location") or None), "description": "Добавлено вручную через /calendarclickup",
                    "task_id": None, "ambiguous_count": None,
                }
            )
            continue
        if not isinstance(ref, int) or not (1 <= ref <= len(actions)) or ref in used_refs:
            return None
        used_refs.add(ref)
        original = dict(actions[ref - 1])
        if original["type"] == "create":
            title = (item.get("title") or original["title"]).strip()
            start_iso = item.get("start") or original["start"]
            end_iso = item.get("end") or original["end"]
            try:
                new_start = datetime.fromisoformat(start_iso)
                new_end = datetime.fromisoformat(end_iso)
            except ValueError:
                return None
            if not title or new_start.tzinfo is None or new_end.tzinfo is None or new_end <= new_start:
                return None
            original.update(
                title=title, start=new_start.isoformat(), end=new_end.isoformat(),
                location=(item.get("location") if "location" in item else original.get("location")) or None,
            )
        elif original["type"] == "rename":
            new_title = (item.get("new_title") or original["new_title"]).strip()
            if not new_title:
                return None
            original["new_title"] = new_title
        revised.append(original)
    order = {"create": 0, "rename": 1, "delete": 2}
    revised.sort(key=lambda a: order[a["type"]])
    return revised
