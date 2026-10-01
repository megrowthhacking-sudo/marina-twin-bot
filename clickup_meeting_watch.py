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
            assignees = task.get("assignees") or []
            if assignees and not any(
                config.CLICKUP_ASSIGNEE_MAP.get(name.lower()) == config.CLICKUP_MEETING_WATCH_ASSIGNEE_ID
                for name in assignees
            ):
                continue
            target_date_by_task_id[task_id] = target_date
            tasks.append(task)
    return tasks, target_date_by_task_id


def _collect_period_meeting_candidates(
    start: datetime, end: datetime, now: datetime,
) -> tuple[list[dict], dict[str, date]]:
    """Общий сбор кандидатов-задач ClickUp за период [start, end) — вынесено 01.10.2026 из
    ensure_period_clickup_meetings_in_calendar в отдельную функцию, чтобы тот же сбор
    использовался и в reconcile_clickup_titles_in_calendar (см. ниже — команда
    /calendarclickup, по прямой просьбе владелицы: сверить её встречи ClickUp с уже
    стоящими в календаре и переименовать те, что названы по-другому). Источники (см.
    были в докстринге ensure_period_clickup_meetings_in_calendar, не повторяем здесь):
    (1) due_date внутри периода, (2) доска WEEKLY TASKS по дню недели в периоде,
    (3) любая задача workspace с явной датой в названии, попадающей в период. Возвращает
    (объединённый по id список сырых задач ClickUp, {task_id: дата дня недели с доски
    WEEKLY TASKS}) — второе нужно вызывающему коду для weekday_hint_date_iso при вызове
    meeting_extractor.extract_meeting_from_task."""
    try:
        due_tasks = clickup_client.get_open_tasks_team_wide(
            assignee_id=config.CLICKUP_MEETING_WATCH_ASSIGNEE_ID,
            due_date_gt_ms=int(start.timestamp() * 1000),
            due_date_lt_ms=int(end.timestamp() * 1000),
            space_ids=None,
        )
    except Exception:
        logger.exception("Не удалось получить задачи ClickUp с due_date в периоде")
        due_tasks = []
    weekly_board_tasks, weekly_target_date_by_task_id = _collect_weekly_board_candidates(now)
    start_date = start.date()
    end_date = end.date()
    weekly_board_tasks = [
        task
        for task in weekly_board_tasks
        if start_date <= weekly_target_date_by_task_id.get(task.get("id"), start_date - timedelta(days=1)) < end_date
    ]
    try:
        all_own_tasks = clickup_client.get_open_tasks_team_wide(
            assignee_id=config.CLICKUP_MEETING_WATCH_ASSIGNEE_ID,
            space_ids=None,
        )
    except Exception:
        logger.exception("Не удалось получить все задачи ClickUp владелицы за период")
        all_own_tasks = []
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
    обратной связи нет.
    space_ids=None (01.10.2026, по прямой просьбе владелицы) — скан, как и у
    /calendarclick, идёт по ВСЕМУ workspace, а не только по config.CLICKUP_MEETING_WATCH_SPACE_IDS
    (РАСПИСАНИЕ + ATLAS). Раньше фон был уже сужен специально, чтобы не захламлять
    календарь встречами коллег (24.09.2026) — это сознательно отменено по новой просьбе
    владелицы: теперь любая похожая на встречу задача, назначенная на неё, из любого
    пространства, авто-ставится в календарь."""
    if not (config.CLICKUP_TEAM_WIDE_ENABLED and config.GOOGLE_CALENDAR_ENABLED and config.OWNER_USER_ID):
        return
    await scan_and_schedule_clickup_meetings(context, space_ids=None)


async def ensure_period_clickup_meetings_in_calendar(start: datetime, end: datetime) -> dict:
    """Часть команды /calendarclick с кнопками периода (добавлено 01.10.2026, по просьбе
    владелицы — раньше /calendarclick показывал только НОВЫЕ, ещё не виденные задачи, из-за
    чего не показывал "все встречи"; см. bot.py::handle_calendarclick_view_callback и
    bot.py::_calendar_period_bounds). В отличие от scan_and_schedule_clickup_meetings (там
    задачи, которые storage.has_seen_clickup_meeting_task уже видел, пропускаются), здесь
    проверка "уже видели" не используется вообще — цель именно показать ВСЁ, что ClickUp
    считает встречей в выбранном периоде, а не только то, что появилось с прошлого скана.
    Безопасно звать повторно для одного и того же периода любое число раз: для каждой
    распознанной встречи зовём calendar_client.create_event, а он сам ищет в календаре
    существующее событие с тем же названием в районе того же времени (окно ±30 минут, см.
    calendar_client._find_duplicate_event) и, если находит, НЕ создаёт новое — просто
    подтверждает, что оно уже есть. Новых дублей в календаре поэтому не возникает.
    Источники кандидатов — по всему workspace (space_ids=None, по той же более ранней
    просьбе владелицы, что и у /calendarclick и у фонового job'а):
    (1) clickup_client.get_open_tasks_team_wide с due_date внутри [start, end);
    (2) доска WEEKLY TASKS (_collect_weekly_board_candidates) — она устроена как "ближайшие
    7 дней от сегодня", поэтому реально даёт кандидатов только если выбранный период
    пересекается с этим окном (для «Сегодня»/«Завтра»/«Текущая неделя» — как правило
    полностью; для «Следующая неделя»/«Текущий месяц» эта доска почти ничего не добавляет —
    у неё просто нет данных о датах дальше недели вперёд, карточка на доске всего одна на
    каждый день недели, не по одной на каждую будущую неделю);
    (3) добавлено 01.10.2026, по просьбе владелицы — ВСЕ открытые задачи workspace,
    назначенные на владелицу, БЕЗ фильтра по due_date/дате создания, клиентски
    отфильтрованные по явной дате в названии (meeting_extractor.parse_explicit_date_time,
    без вызова Claude — дёшево), попадающей в [start, end). Это снимает ограничение
    источника (2): теперь сотрудники пишут дату/время прямо в названии задачи (формат
    "дата, время, компания, тип, тема" — договорённость от 01.10.2026), due_date в ClickUp
    при этом может быть не заполнен вовсе, поэтому такие задачи не попадали бы ни в (1),
    ни в (2) для дальних периодов («Следующая неделя»/«Текущий месяц») — здесь ищем их
    напрямую по тексту названия, независимо от того, насколько далеко вперёд стоит дата.
    Возвращает {"scanned": int, "created_or_confirmed": int, "errors": int} — только для
    лога; сама команда после вызова показывает владелице финальный список обычным
    calendar_client.list_events, а не то, что вернула эта функция, — так в списке видны и
    уже существовавшие ручные встречи, и только что подтверждённые из ClickUp, одним
    вызовом."""
    stats: dict = {"scanned": 0, "created_or_confirmed": 0, "errors": 0}
    tz = ZoneInfo(config.MARINATWIN_TIMEZONE)
    now = datetime.now(tz)
    tasks, weekly_target_date_by_task_id = _collect_period_meeting_candidates(start, end, now)
    for task in tasks:
        task_id = task.get("id")
        if not task_id:
            continue
        stats["scanned"] += 1
        try:
            full_task = clickup_client.get_task(task_id)
        except Exception:
            logger.exception("Не удалось прочитать задачу ClickUp %s для /calendarclick за период", task_id)
            stats["errors"] += 1
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
            logger.exception("Ошибка разбора задачи ClickUp %s на предмет встречи (/calendarclick период)", task_id)
            stats["errors"] += 1
            continue
        if not meeting:
            continue
        try:
            meeting_start = datetime.fromisoformat(meeting["start"]).astimezone(tz)
        except (ValueError, KeyError, TypeError):
            continue
        if not (start <= meeting_start < end):
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
                "Не удалось создать/подтвердить событие календаря для задачи ClickUp %s («%s»)",
                task_id, task.get("name"),
            )
            stats["errors"] += 1
            continue
        storage.mark_seen_clickup_meeting_task(task_id)
        stats["created_or_confirmed"] += 1
    return stats


async def reconcile_clickup_titles_in_calendar(horizon_days: int = 7) -> dict:
    """/calendarclickup (добавлено 01.10.2026, по прямой просьбе владелицы): сверяет её
    встречи ClickUp за ближайшие horizon_days дней (владелица попросила неделю — см.
    bot.py::handle_calendarclickup_command) с личным календарём (m@altyn.one) и, если
    встреча УЖЕ стоит в календаре на то же время, но названа по-другому — ПЕРЕПИСЫВАЕТ
    название события на то, как оно написано в ClickUp (calendar_client.update_event).
    Если встречи в календаре в это время вовсе нет — создаёт её (как
    ensure_period_clickup_meetings_in_calendar//calendarclick, по прямой просьбе
    владелицы — эта команда одновременно и достраивает отсутствующие встречи, и чистит
    разночтения в названиях уже существующих).

    В отличие от calendar_client.create_event (дедуп по СОВПАДАЮЩЕМУ названию в окне
    ±30 минут — см. calendar_client._find_duplicate_event) здесь сопоставление идёт по
    ВРЕМЕНИ, а не по названию: иначе разница в названии помешала бы узнать, что это та же
    встреча, и привела бы к дублю вместо переименования. Если в окне ±30 минут вокруг
    времени встречи найдено РОВНО ОДНО существующее событие — либо подтверждаем совпадение
    (названия совпали, ничего не делаем), либо переименовываем его. Если не найдено ни
    одного — создаём новое событие, как ensure_period_clickup_meetings_in_calendar. Если
    найдено НЕСКОЛЬКО событий в одном окне — непонятно, какое из них "то самое" (и
    переименовывать наугад — опасно), поэтому НЕ трогаем ни одно из существующих, а
    добавляем в это же время ЕЩЁ ОДНО новое событие с названием из ClickUp (исправлено
    01.10.2026, по прямой просьбе владелицы — раньше такие задачи просто пропускались и
    могли вообще не попасть в календарь); такая задача попадает сразу и в
    stats["created"], и в stats["ambiguous"] — владелица видит в отчёте, что встреча
    поставлена, но рядом есть другие события того же времени, которые стоит проверить
    вручную (возможно, старые дубли пора убрать).

    Источники кандидатов — те же три, что и у ensure_period_clickup_meetings_in_calendar
    (см. _collect_period_meeting_candidates): due_date в периоде, доска WEEKLY TASKS,
    явная дата в названии любой задачи workspace.

    Возвращает {"scanned": int, "renamed": [{"old_title", "new_title", "when"}, ...],
    "created": [{"title", "when"}, ...], "unchanged": int, "ambiguous": [{"title", "when",
    "count"}, ...], "errors": int} — используется bot.py::handle_calendarclickup_command
    для итогового отчёта владелице."""
    stats: dict = {
        "scanned": 0, "renamed": [], "created": [], "unchanged": 0, "ambiguous": [], "errors": 0,
    }
    tz = ZoneInfo(config.MARINATWIN_TIMEZONE)
    now = datetime.now(tz)
    start = now
    end = now + timedelta(days=horizon_days)
    tasks, weekly_target_date_by_task_id = _collect_period_meeting_candidates(start, end, now)

    for task in tasks:
        task_id = task.get("id")
        if not task_id:
            continue
        stats["scanned"] += 1
        try:
            full_task = clickup_client.get_task(task_id)
        except Exception:
            logger.exception("Не удалось прочитать задачу ClickUp %s для /calendarclickup", task_id)
            stats["errors"] += 1
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
            stats["errors"] += 1
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

        try:
            nearby = calendar_client.list_events(
                (meeting_start - timedelta(minutes=30)).isoformat(),
                (meeting_end + timedelta(minutes=30)).isoformat(),
            )
        except Exception:
            logger.exception("Не удалось прочитать календарь рядом с %s для /calendarclickup", meeting_start)
            stats["errors"] += 1
            continue
        nearby = [e for e in nearby if not e.get("all_day")]
        when = meeting_start.strftime("%d.%m %H:%M")

        if not nearby:
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
                    "Не удалось создать событие для задачи ClickUp %s (/calendarclickup)", task_id,
                )
                stats["errors"] += 1
                continue
            storage.mark_seen_clickup_meeting_task(task_id)
            stats["created"].append({"title": meeting["title"], "when": when})
            continue

        if len(nearby) > 1:
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
                    "Не удалось создать доп. событие для неоднозначного времени, задача ClickUp %s "
                    "(/calendarclickup)",
                    task_id,
                )
                stats["errors"] += 1
                continue
            storage.mark_seen_clickup_meeting_task(task_id)
            stats["created"].append({"title": meeting["title"], "when": when})
            stats["ambiguous"].append({"title": meeting["title"], "when": when, "count": len(nearby)})
            continue

        existing = nearby[0]
        if existing.get("title", "").strip().lower() == meeting["title"].strip().lower():
            stats["unchanged"] += 1
            continue

        event_id = existing.get("id")
        if not event_id:
            stats["ambiguous"].append({"title": meeting["title"], "when": when, "count": 1})
            continue
        try:
            calendar_client.update_event(event_id, title=meeting["title"])
        except Exception:
            logger.exception(
                "Не удалось переименовать событие календаря %s в «%s» (/calendarclickup)",
                event_id, meeting["title"],
            )
            stats["errors"] += 1
            continue
        stats["renamed"].append(
            {"old_title": existing.get("title", ""), "new_title": meeting["title"], "when": when}
        )

    return stats
