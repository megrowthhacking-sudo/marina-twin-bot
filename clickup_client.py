"""
Тонкий клиент над ClickUp API v2 — создание задач и чтение уже существующих
(живых) задач списка, напрямую из ClickUp (см. get_open_tasks).
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
# Обратная карта — для чтения приоритета из ответа ClickUp (get_open_tasks).
_PRIORITY_NAMES = {1: "urgent", 2: "high", 3: "normal", 4: "low"}


def _headers() -> dict:
    return {
        "Authorization": config.CLICKUP_API_TOKEN,
        "Content-Type": "application/json",
    }


def create_task(list_id: str, name: str, description: str = "", priority: str | None = None) -> dict:
    """Создаёт задачу в указанном списке ClickUp (list_id — конкретный проектный список,
    см. config.CLICKUP_LIST_IDS). Бросает исключение при ошибке — вызывающий код (bot.py)
    сам решает, как это залогировать и не уронить остальную выгрузку."""
    if not config.CLICKUP_API_TOKEN:
        raise RuntimeError("ClickUp не настроен (нет CLICKUP_API_TOKEN)")

    payload: dict = {"name": name[:255], "description": description[:8000]}
    priority_num = PRIORITY_MAP.get((priority or "").lower())
    if priority_num:
        payload["priority"] = priority_num

    url = f"{BASE_URL}/list/{list_id}/task"
    resp = requests.post(url, headers=_headers(), json=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()


def _extract_priority(raw_task: dict) -> str | None:
    """ClickUp отдаёт приоритет как объект {"id": "1", "priority": "urgent", ...} либо
    None, если приоритет не задан. Нормализуем к одному из ключей PRIORITY_MAP, либо None."""
    priority = raw_task.get("priority")
    if not priority:
        return None
    name = (priority.get("priority") or "").lower().strip()
    if name in PRIORITY_MAP:
        return name
    try:
        return _PRIORITY_NAMES.get(int(priority.get("id")))
    except (TypeError, ValueError):
        return None


def get_open_tasks(list_id: str) -> list[dict]:
    """Возвращает актуальные (открытые, не в архиве) задачи списка ClickUp — читает их
    напрямую из ClickUp API, а не из локального журнала pushed_tasks, поэтому отражает
    и то, что было создано/изменено вручную прямо в ClickUp (см. _fetch_project_tasks
    в bot.py). Пробегает все страницы ответа (ClickUp отдаёт максимум 100 задач за раз).

    Каждый элемент результата — {"id", "name", "priority", "date_created", "url"}, где
    priority — один из "urgent"/"high"/"normal"/"low"/None, date_created — unix-время в
    секундах. Список отсортирован по date_created по возрастанию (сначала старые).

    Бросает RuntimeError, если CLICKUP_API_TOKEN не задан, и requests.HTTPError при
    ошибке API — вызывающий код сам решает, как это обработать (см. _fetch_project_tasks)."""
    if not config.CLICKUP_API_TOKEN:
        raise RuntimeError("ClickUp не настроен (нет CLICKUP_API_TOKEN)")

    tasks: list[dict] = []
    page = 0
    while True:
        resp = requests.get(
            f"{BASE_URL}/list/{list_id}/task",
            headers=_headers(),
            params={"archived": "false", "page": page, "order_by": "created", "reverse": "false"},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        raw_tasks = data.get("tasks") or []
        for raw_task in raw_tasks:
            try:
                date_created = int(raw_task.get("date_created")) // 1000
            except (TypeError, ValueError):
                date_created = 0
            tasks.append(
                {
                    "id": str(raw_task.get("id", "")),
                    "name": raw_task.get("name", ""),
                    "priority": _extract_priority(raw_task),
                    "date_created": date_created,
                    "url": raw_task.get("url", ""),
                }
            )
        if data.get("last_page", True) or not raw_tasks:
            break
        page += 1

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
