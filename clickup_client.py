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


def create_task(
    list_id: str,
    name: str,
    description: str = "",
    priority: str | None = None,
    assignees: list[int] | None = None,
    start_date_ms: int | None = None,
    due_date_ms: int | None = None,
) -> dict:
    """Создаёт задачу в указанном списке ClickUp (list_id — конкретный проектный список,
    см. config.CLICKUP_LIST_IDS). assignees — список ClickUp user_id (см.
    config.CLICKUP_ASSIGNEE_MAP), можно не указывать. start_date_ms/due_date_ms — unix-время
    в МИЛЛИСЕКУНДАХ (не секундах — так требует ClickUp API), если нужно проставить время
    начала/дедлайна с точностью до часа (см. bot.py::_mirror_meeting_to_clickup — зеркало
    встреч Google Calendar в список "Расписание Марина Twin"); без них задача создаётся
    без дат, как раньше. Бросает исключение при ошибке — вызывающий код (bot.py) сам
    решает, как это залогировать и не уронить остальную выгрузку."""
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

    url = f"{BASE_URL}/list/{list_id}/task"
    resp = requests.post(url, headers=_headers(), json=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()


def get_open_tasks(list_id: str, assignee_id: int | None = None) -> list[dict]:
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
    Возвращает список словарей {"id", "name", "priority" (urgent/high/normal/low/None),
    "date_created" (unix-время в секундах), "due_date" (unix-время в секундах или None,
    если срок не задан в ClickUp), "url"}, по возрастанию даты создания. Бросает
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
    "url", "list_name"} — "list_name" (может быть None) добавлен специально для этой
    функции, чтобы в отчёте по сотруднику было видно, из какого списка/проекта задача,
    раз теперь они могут быть откуда угодно. Бросает исключение при ошибке сети/API —
    вызывающий код сам решает, как это залогировать и что ответить пользователю."""
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
            tasks.append(
                {
                    "id": t.get("id"),
                    "name": t.get("name") or "(без названия)",
                    "priority": priority,
                    "date_created": created,
                    "due_date": due_date,
                    "url": t.get("url"),
                    "list_name": list_field.get("name"),
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
