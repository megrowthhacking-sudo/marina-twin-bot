"""
Тонкий клиент над ClickUp API v2 — создание и чтение задач.
Авторизация — личный токен в заголовке Authorization (без "Bearer").
Документация: https://developer.clickup.com/reference/createtask,
https://developer.clickup.com/reference/gettasks
"""

import logging

import requests

import config

logger = logging.getLogger(__name__)

BASE_URL = "https://api.clickup.com/api/v2"

# ClickUp просит приоритет числом: 1=Urgent, 2=High, 3=Normal, 4=Low.
PRIORITY_MAP = {"urgent": 1, "high": 2, "normal": 3, "low": 4}


def _headers() -> dict:
    return {
        "Authorization": config.CLICKUP_API_TOKEN,
        "Content-Type": "application/json",
    }


def _extract_assignee_names(task_json: dict) -> list[str]:
    """Имена ответственных прямо из ClickUp-объекта задачи (поле "assignees", отдаёт сам
    ClickUp API — не путать с локальным assignee_name из task_extractor.py, который лишь
    свободный текст на момент СОЗДАНИЯ задачи). Используется, чтобы в отчётах (см. bot.py,
    часть 33, "на кого задача") показывать живое, актуальное назначение — в том числе для
    задач, назначенных/переназначенных вручную прямо в ClickUp, а не только ботом. Берём
    "username" (реальное отображаемое имя ClickUp-аккаунта); если вдруг его нет — email как
    запасной вариант; если и его нет — пропускаем эту запись, а не подставляем None/пусто."""
    names = []
    for a in task_json.get("assignees") or []:
        name = a.get("username") or a.get("email")
        if name:
            names.append(name)
    return names


def create_task(
    list_id: str,
    name: str,
    description: str = "",
    priority: str | None = None,
    assignees: list[int] | None = None,
    start_date_ms: int | None = None,
    due_date_ms: int | None = None,
    status: str | None = None,
) -> dict:
    """Создаёт задачу в указанном списке ClickUp (list_id — конкретный проектный список,
    см. config.CLICKUP_LIST_IDS). assignees — список ClickUp user_id (см.
    config.CLICKUP_ASSIGNEE_MAP), можно не указывать. start_date_ms/due_date_ms — unix-время
    в МИЛЛИСЕКУНДАХ (не секундах — так требует ClickUp API), если нужно проставить время
    начала/дедлайна с точностью до часа (см. bot.py::_mirror_meeting_to_clickup — зеркало
    встреч Google Calendar в список "Расписание Марина Twin"); без них задача создаётся
    без дат, как раньше. status — точное имя статуса ЭТОГО списка (например "Понедельник"
    для WEEKLY TASKS) — используется явной постановкой задачи по просьбе владелицы (см.
    bot.py::_propose_explicit_task_command/handle_manual_task_callback, task_command.py);
    вызывающий код обязан заранее проверить, что такой статус реально существует в
    списке (см. get_list_statuses ниже) — сам ClickUp при неизвестном имени статуса просто
    вернёт ошибку. Без указания — задача создаётся с дефолтным статусом списка, как раньше.
    Бросает исключение при ошибке — вызывающий код (bot.py) сам решает, как это
    залогировать и не уронить остальную выгрузку."""
    if not config.CLICKUP_API_TOKEN:
        raise RuntimeError("ClickUp не настроен (нет CLICKUP_API_TOKEN)")

    payload: dict = {"name": name[:255], "description": description[:8000]}
    priority_num = PRIORITY_MAP.get((priority or "").lower())
    if priority_num:
        payload["priority"] = priority_num
    if assignees:
        payload["assignees"] = assignees
    if start_date_ms is not None:
        payload["start_date"] = start_date_ms
        payload["start_date_time"] = True
    if due_date_ms is not None:
        payload["due_date"] = due_date_ms
        payload["due_date_time"] = True
    if status:
        payload["status"] = status

    url = f"{BASE_URL}/list/{list_id}/task"
    resp = requests.post(url, headers=_headers(), json=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()


def get_open_tasks(
    list_id: str, assignee_id: int | None = None, statuses: list[str] | None = None
) -> list[dict]:
    """Тянет реальные ОТКРЫТЫЕ (незавершённые) задачи списка прямо из ClickUp — источник
    истины для отчётов по проектам (/tasksX, /tasksall, /urgent, утренний дайджест —
    все они сознательно ограничены 4 официальными проектными списками), в отличие от
    локального журнала когда-либо созданных ботом задач (тот не узнаёт о том, что
    задачу закрыли или поменяли напрямую в ClickUp, минуя бота). Персональные команды
    по сотрудникам (/lili /olga ... — см. bot.py::_send_employee_report) с 06.09
    используют НЕ эту функцию, а get_open_tasks_team_wide ниже (по всему ClickUp, не
    только эти 4 списка) — эта функция осталась только для проектных команд.
    assignee_id — если задан, фильтрует на стороне ClickUp API (параметр
    "assignees[]») и возвращает только задачи, назначенные на этого человека
    (config.CLICKUP_ASSIGNEE_MAP); без него — все открытые задачи списка, как раньше.
    statuses — если задан, фильтрует на стороне ClickUp API (параметр "statuses[]») и
    возвращает только задачи с одним из этих статусов (используется командами по
    статусам списка WEEKLY TASKS — /unsorted /atlas /monday и т.д., см.
    config.CLICKUP_WEEKLY_STATUS_COMMANDS/bot.py::_send_weekly_status_report); без него —
    все открытые задачи списка, как раньше.
    Возвращает список словарей {"id", "name", "priority" (urgent/high/normal/low/None),
    "date_created" (unix-время в секундах), "due_date" (unix-время в секундах или None,
    если срок не задан в ClickUp), "url", "tags" (список имён тегов задачи — нужно, чтобы
    отличать задачи, помеченные "🔥 Горит», см. bot.py::_is_fire)}, по возрастанию даты
    создания. Бросает
    исключение при ошибке сети/API — вызывающий код сам решает, как это залогировать и
    что ответить пользователю."""
    if not config.CLICKUP_API_TOKEN:
        raise RuntimeError("ClickUp не настроен (нет CLICKUP_API_TOKEN)")
    tasks: list[dict] = []
    page = 0
    while True:
        params = {"archived": "false", "page": page, "order_by": "created", "reverse": "false"}
        if assignee_id is not None:
            params["assignees[]"] = [assignee_id]
        if statuses:
            params["statuses[]"] = statuses
        resp = requests.get(
            f"{BASE_URL}/list/{list_id}/task",
            headers=_headers(),
            params=params,
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("tasks") or []
        for t in batch:
            priority_field = t.get("priority") or {}
            priority = (priority_field.get("priority") or "").lower() or None
            try:
                created = float(t.get("date_created") or 0) / 1000
            except (TypeError, ValueError):
                created = 0.0
            raw_due = t.get("due_date")
            try:
                due_date = float(raw_due) / 1000 if raw_due else None
            except (TypeError, ValueError):
                due_date = None
            tasks.append(
                {
                    "id": t.get("id"),
                    "name": t.get("name") or "(без названия)",
                    "priority": priority,
                    "date_created": created,
                    "due_date": due_date,
                    "url": t.get("url"),
                    "tags": [tg.get("name") for tg in t.get("tags") or [] if tg.get("name")],
                    "assignees": _extract_assignee_names(t),
                }
            )
        if data.get("last_page", True) or not batch:
            break
        page += 1
    tasks.sort(key=lambda t: t["date_created"])
    return tasks


def get_open_tasks_team_wide(assignee_id: int | None = None) -> list[dict]:
    """Тянет ОТКРЫТЫЕ задачи по ВСЕМУ workspace ClickUp (config.CLICKUP_TEAM_ID) — все
    пространства/папки/списки, а не только 4 официальных проектных списка (см.
    get_open_tasks выше). Добавлено 06.09 по прямой просьбе владелицы: персональные
    команды по сотрудникам (/lili /olga /sveta /ilya /nazgul /alex /ub /marina — см.
    bot.py::_send_employee_report) должны находить задачи человека ГДЕ БЫ они ни были
    заведены, включая личные папки/пространства вне 4 официальных проектов.

    Использует ClickUp "Get Filtered Team Tasks" (`GET /team/{team_id}/task`) —
    в отличие от списочного `GET /list/{list_id}/task`, этот эндпоинт ищет по всему
    workspace сразу. assignee_id — тот же смысл, что в get_open_tasks (серверная
    фильтрация ClickUp API через "assignees[]»); без него возвращает вообще ВСЕ
    открытые задачи workspace (используется для последующей клиентской фильтрации по
    текстовому префиксу имени — см. config.EMPLOYEE_COMMANDS, случай Саши, у которого
    нет реального ClickUp-аккаунта). include_closed=false — как и у get_open_tasks,
    закрытые задачи не возвращаются. Постранично, 100 задач за раз; у этого эндпоинта
    ClickUp не отдаёт явный флаг "последняя страница" (в отличие от списочного) —
    признак конца пагинации: страница вернула меньше 100 задач. Захардкожен потолок в
    50 страниц (5000 задач) на случай сбоя пагинации — при его достижении в лог пишется
    предупреждение, но накопленное уже возвращается, а не теряется.

    Возвращает список словарей {"id", "name", "priority", "date_created", "due_date",
    "url", "tags", "list_name", "folder_name", "space_id"} — "list_name"/"folder_name"
    (могут быть None) и "space_id" добавлены специально для этой функции, чтобы в отчёте
    по сотруднику было видно, из какого пространства/папки/списка задача (по прямой
    просьбе владелицы, часть 27 — см. bot.py::_format_task_location), раз теперь они
    могут быть откуда угодно; ClickUp подставляет "folder": {"name": "hidden"} у списков
    без реальной папки (лежащих прямо в пространстве) — такое имя отфильтровывается в
    None, это не настоящее название папки. "space_id" — сам ClickUp API не отдаёт имя
    пространства прямо в объекте задачи, только id (см. config.CLICKUP_SPACE_NAMES —
    сопоставление сделано вручную по данным живого запроса
    clickup_get_workspace_hierarchy, а не через отдельный API-вызов на каждую задачу).
    Бросает исключение при ошибке сети/API — вызывающий код сам решает, как это
    залогировать и что ответить пользователю."""
    if not config.CLICKUP_API_TOKEN:
        raise RuntimeError("ClickUp не настроен (нет CLICKUP_API_TOKEN)")
    if not config.CLICKUP_TEAM_ID:
        raise RuntimeError("ClickUp workspace-id не настроен (нет CLICKUP_TEAM_ID)")
    tasks: list[dict] = []
    page = 0
    _MAX_PAGES = 50
    while page < _MAX_PAGES:
        params = {
            "page": page,
            "order_by": "created",
            "reverse": "false",
            "include_closed": "false",
            "subtasks": "true",
        }
        if assignee_id is not None:
            params["assignees[]"] = [assignee_id]
        resp = requests.get(
            f"{BASE_URL}/team/{config.CLICKUP_TEAM_ID}/task",
            headers=_headers(),
            params=params,
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("tasks") or []
        for t in batch:
            priority_field = t.get("priority") or {}
            priority = (priority_field.get("priority") or "").lower() or None
            try:
                created = float(t.get("date_created") or 0) / 1000
            except (TypeError, ValueError):
                created = 0.0
            raw_due = t.get("due_date")
            try:
                due_date = float(raw_due) / 1000 if raw_due else None
            except (TypeError, ValueError):
                due_date = None
            list_field = t.get("list") or {}
            folder_field = t.get("folder") or {}
            space_field = t.get("space") or {}
            folder_name = folder_field.get("name")
            if folder_name and folder_name.strip().lower() == "hidden":
                folder_name = None
            tasks.append(
                {
                    "id": t.get("id"),
                    "name": t.get("name") or "(без названия)",
                    "priority": priority,
                    "date_created": created,
                    "due_date": due_date,
                    "url": t.get("url"),
                    "tags": [tg.get("name") for tg in t.get("tags") or [] if tg.get("name")],
                    "list_name": list_field.get("name"),
                    "folder_name": folder_name,
                    "space_id": space_field.get("id"),
                    "assignees": _extract_assignee_names(t),
                }
            )
        if len(batch) < 100:
            break
        page += 1
    else:
        logger.warning(
            "get_open_tasks_team_wide: остановлено на потолке в %d страниц — возможно, "
            "получены не все задачи workspace",
            _MAX_PAGES,
        )
    tasks.sort(key=lambda t: t["date_created"])
    return tasks


def get_task(task_id: str) -> dict | None:
    """Читает одну задачу по id — нужна кнопкам под отчётами по сотрудникам (см.
    bot.py::handle_employee_task_callback), когда на руках только task_id из
    callback_data и нужно узнать актуальное имя (для подтверждения удаления), id её
    списка (чтобы понять, каким статусом закрывать при "✅ Сделано" — см.
    get_list_closed_status/mark_task_done ниже), id её пространства (чтобы завести тег
    "кричащая задача", если его ещё нет в этом пространстве — см. ensure_tag_on_task) или
    её текущие теги (чтобы понять, стоит ли уже пометка "🔥 Горит» — см. bot.py::_is_fire).
    None, если задача не найдена (уже удалена — например, кто-то удалил её напрямую в
    ClickUp между отправкой отчёта и нажатием кнопки)."""
    if not config.CLICKUP_API_TOKEN:
        raise RuntimeError("ClickUp не настроен (нет CLICKUP_API_TOKEN)")
    resp = requests.get(f"{BASE_URL}/task/{task_id}", headers=_headers(), timeout=15)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    data = resp.json()
    list_field = data.get("list") or {}
    space_field = data.get("space") or {}
    return {
        "id": data.get("id"),
        "name": data.get("name") or "(без названия)",
        "list_id": list_field.get("id"),
        "space_id": space_field.get("id"),
        "tags": [tg.get("name") for tg in data.get("tags") or [] if tg.get("name")],
    }


def get_list_closed_status(list_id: str) -> str | None:
    """Имя статуса с типом "closed" (реально закрывающего задачу) для конкретного
    списка ClickUp. Нужно отдельной функцией, а не жёстко захардкоженным именем вроде
    "Done"/"Готово", потому что персональные команды по сотрудникам с 06.09 ищут задачи
    по ВСЕМУ workspace (см. get_open_tasks_team_wide) — а в разных пространствах/списках
    ClickUp набор кастомных статусов может называться по-разному ("Готово", "Закрыто",
    "Complete" и т.п.), общего для всех статуса не существует. None, если у списка
    почему-то нет статуса с type == "closed" (в норме такого не бывает — у любого списка
    ClickUp есть хотя бы один закрывающий статус, но лучше явно обработать, чем упасть)."""
    if not config.CLICKUP_API_TOKEN:
        raise RuntimeError("ClickUp не настроен (нет CLICKUP_API_TOKEN)")
    resp = requests.get(f"{BASE_URL}/list/{list_id}", headers=_headers(), timeout=15)
    resp.raise_for_status()
    data = resp.json()
    for status in data.get("statuses") or []:
        if (status.get("type") or "").lower() == "closed":
            return status.get("status")
    return None


def get_list_statuses(list_id: str) -> list[str]:
    """Все имена статусов списка, как они настроены в самом ClickUp (не только закрывающий,
    см. get_list_closed_status выше) — нужно для явной постановки задачи в конкретный
    статус (по прямой просьбе владелицы, 06.09: "поставь задачу в WEEKLY в статус
    Понедельник", см. bot.py::_propose_explicit_task_command/task_command.py). Перед
    созданием задачи с явно названным статусом сверяем его с этим реальным списком —
    имена статусов у разных списков ClickUp произвольные (не общий словарь), и лучше
    честно сказать владелице, какие статусы есть на самом деле, чем создать задачу с
    выдуманным именем и получить ошибку от ClickUp API."""
    if not config.CLICKUP_API_TOKEN:
        raise RuntimeError("ClickUp не настроен (нет CLICKUP_API_TOKEN)")
    resp = requests.get(f"{BASE_URL}/list/{list_id}", headers=_headers(), timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return [s.get("status") for s in data.get("statuses") or [] if s.get("status")]


def set_task_status(task_id: str, status_name: str) -> None:
    """Ставит задаче статус по имени (как он называется в списке этой конкретной
    задачи — см. get_list_closed_status). Бросает исключение при ошибке сети/API."""
    if not config.CLICKUP_API_TOKEN:
        raise RuntimeError("ClickUp не настроен (нет CLICKUP_API_TOKEN)")
    resp = requests.put(
        f"{BASE_URL}/task/{task_id}", headers=_headers(), json={"status": status_name}, timeout=20,
    )
    resp.raise_for_status()


def mark_task_done(task_id: str) -> None:
    """Закрывает задачу — по кнопке "✅ Сделано" под отчётом по сотруднику (по прямой
    просьбе владелицы, 06.09). Сначала узнаёт задачу и id её списка (get_task), затем
    закрывающий статус этого списка (get_list_closed_status), и только потом ставит его
    (set_task_status) — чтобы задача реально попала в "выполненные" именно этого списка,
    а не осталась в каком-то промежуточном кастомном статусе. Бросает исключение, если
    задача не найдена (уже удалена) или у её списка почему-то нет closed-статуса —
    вызывающий код (bot.py) сам решает, как это показать владелице."""
    task = get_task(task_id)
    if not task or not task.get("list_id"):
        raise RuntimeError("Задача не найдена в ClickUp (возможно, уже удалена или закрыта)")
    closed_status = get_list_closed_status(task["list_id"])
    if not closed_status:
        raise RuntimeError(f"Не нашла статус \"выполнено\" для списка {task['list_id']}")
    set_task_status(task_id, closed_status)


def set_task_priority(task_id: str, priority: str) -> None:
    """Ставит задаче приоритет (urgent/high/normal/low, см. PRIORITY_MAP) — по кнопке
    "🔴 Срочная" под отчётом по сотруднику (по прямой просьбе владелицы, 06.09)."""
    if not config.CLICKUP_API_TOKEN:
        raise RuntimeError("ClickUp не настроен (нет CLICKUP_API_TOKEN)")
    priority_num = PRIORITY_MAP.get((priority or "").lower())
    if not priority_num:
        raise ValueError(f"Неизвестный приоритет: {priority!r}")
    resp = requests.put(
        f"{BASE_URL}/task/{task_id}", headers=_headers(), json={"priority": priority_num}, timeout=20,
    )
    resp.raise_for_status()


def delete_task(task_id: str) -> None:
    """Удаляет задачу из ClickUp БЕЗВОЗВРАТНО — по кнопке "🗑 Удалить" под отчётом по
    сотруднику, только после явного подтверждения владелицей (см.
    bot.py::handle_employee_task_callback, действие "delyes" — шаг подтверждения
    добавлен по её же прямой просьбе, риск случайного нажатия на маленькой кнопке в
    телефоне на необратимое действие)."""
    if not config.CLICKUP_API_TOKEN:
        raise RuntimeError("ClickUp не настроен (нет CLICKUP_API_TOKEN)")
    resp = requests.delete(f"{BASE_URL}/task/{task_id}", headers=_headers(), timeout=20)
    resp.raise_for_status()


def move_task_to_list(task_id: str, list_id: str) -> None:
    """Переносит задачу в другой список ClickUp — по прямой просьбе владелицы (5-я кнопка
    "📆 Weekly" под отчётами по сотрудникам, см. bot.py::handle_employee_task_callback,
    действие "weekly"): формально это "Add Task To List" (POST
    /v2/list/{list_id}/task/{task_id}) — эндпоинт ClickUp для мульти-списковой функции
    "Tasks in Multiple Lists" (добавляет задачу ДОПОЛНИТЕЛЬНО в другой список, не убирая
    из исходного). Живой тест в реальном рабочем пространстве Марины (эта функция ClickApp
    там не включена) подтвердил, что при отключённой мульти-списковости этот же вызов
    реально ПЕРЕНОСИТ задачу — "родной" список задачи становится list_id, дублирования не
    происходит. Если в будущем в workspace включат многосписочность, поведение может
    измениться на настоящее мультисписковое добавление — тогда потребуется отдельно убирать
    задачу из старого списка. Бросает исключение при ошибке сети/API."""
    if not config.CLICKUP_API_TOKEN:
        raise RuntimeError("ClickUp не настроен (нет CLICKUP_API_TOKEN)")
    resp = requests.post(f"{BASE_URL}/list/{list_id}/task/{task_id}", headers=_headers(), timeout=20)
    resp.raise_for_status()


def add_tag_to_task(task_id: str, tag_name: str) -> None:
    """Ставит существующий тег на задачу. ClickUp требует, чтобы тег с таким именем уже
    существовал в ПРОСТРАНСТВЕ (space) этой задачи — иначе вызов падает с ошибкой (см.
    ensure_tag_on_task ниже, которая сама заводит тег при необходимости). Бросает
    исключение при ошибке сети/API."""
    if not config.CLICKUP_API_TOKEN:
        raise RuntimeError("ClickUp не настроен (нет CLICKUP_API_TOKEN)")
    resp = requests.post(f"{BASE_URL}/task/{task_id}/tag/{tag_name}", headers=_headers(), timeout=15)
    resp.raise_for_status()


def remove_tag_from_task(task_id: str, tag_name: str) -> None:
    """Снимает тег с задачи (сам тег в пространстве при этом не удаляется, только связь
    с этой конкретной задачей). Бросает исключение при ошибке сети/API."""
    if not config.CLICKUP_API_TOKEN:
        raise RuntimeError("ClickUp не настроен (нет CLICKUP_API_TOKEN)")
    resp = requests.delete(f"{BASE_URL}/task/{task_id}/tag/{tag_name}", headers=_headers(), timeout=15)
    resp.raise_for_status()


def create_space_tag(space_id: str, tag_name: str, fg: str = "#ffffff", bg: str = "#e50000") -> None:
    """Заводит новый тег в пространстве ClickUp (нужен один раз на каждое пространство —
    см. ensure_tag_on_task ниже). fg/bg — цвет текста/фона тега в ClickUp UI, по умолчанию
    белым по красному (визуально соответствует "🔥 Горит»/срочности). Бросает исключение
    при ошибке сети/API — в т.ч. если тег с таким именем в этом пространстве уже есть
    (вызывающий код должен считать это неопасным и просто повторить добавление тега на
    задачу, см. ensure_tag_on_task)."""
    if not config.CLICKUP_API_TOKEN:
        raise RuntimeError("ClickUp не настроен (нет CLICKUP_API_TOKEN)")
    resp = requests.post(
        f"{BASE_URL}/space/{space_id}/tag",
        headers=_headers(),
        json={"tag": {"name": tag_name, "tag_fg": fg, "tag_bg": bg}},
        timeout=15,
    )
    resp.raise_for_status()


def ensure_tag_on_task(task_id: str, tag_name: str, space_id: str | None = None) -> None:
    """Ставит тег на задачу, при необходимости заранее заведя его в пространстве этой
    задачи — по прямой просьбе владелицы (часть 27, кнопка "🔥 Горит» теперь ставит
    настоящий ClickUp-тег "кричащая задача», см. config.CLICKUP_FIRE_TAG_NAME, а не только
    локальную пометку внутри бота, как раньше в части 24). ClickUp не заводит
    отсутствующий тег автоматически при добавлении на задачу (add_tag_to_task падает с
    ошибкой) — здесь это на первый неудачный вызов ловится, тег заводится в пространстве
    задачи (create_space_tag) и добавление повторяется. space_id можно передать заранее,
    если уже известен (см. bot.py::handle_employee_task_callback — там задача уже прочитана
    целиком через get_task), иначе функция сама прочитает задачу, чтобы его узнать. Бросает
    исключение, если задача не найдена, у неё не определить пространство, или создание
    тега/повторное добавление тоже не удалось."""
    try:
        add_tag_to_task(task_id, tag_name)
        return
    except requests.HTTPError:
        pass
    if space_id is None:
        task = get_task(task_id)
        space_id = task.get("space_id") if task else None
    if not space_id:
        raise RuntimeError(f"Не удалось определить пространство задачи {task_id} для тега «{tag_name}»")
    try:
        create_space_tag(space_id, tag_name)
    except requests.HTTPError:
        # Скорее всего тег уже существует (создан раньше или гонка одновременных нажатий) —
        # не страшно, дальше просто пробуем добавить его на задачу ещё раз.
        pass
    add_tag_to_task(task_id, tag_name)


def test_connection(list_id: str) -> tuple[bool, str]:
    """Простая проверка токена/списка — дергает конкретный список, ничего не создавая.
    Удобно для ручной диагностики после деплоя (см. DEPLOY.md)."""
    if not config.CLICKUP_API_TOKEN:
        return False, "CLICKUP_API_TOKEN не задан"
    try:
        resp = requests.get(
            f"{BASE_URL}/list/{list_id}",
            headers=_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return True, f"Список найден: «{data.get('name', '?')}»"
    except requests.HTTPError as e:
        return False, f"ClickUp вернул ошибку: {e.response.status_code} {e.response.text[:200]}"
    except Exception as e:  # noqa: BLE001
        return False, f"Не удалось связаться с ClickUp: {e}"
