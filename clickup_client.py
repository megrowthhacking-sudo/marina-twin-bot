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


def get_open_tasks(list_id: str) -> list[dict]:
    """Тянет реальные ОТКРЫТЫЕ (незавершённые) задачи списка прямо из ClickUp — источник
    истины для отчётов (/tasksX, /urgent, утренний дайджест), в отличие от локального
    журнала когда-либо созданных ботом задач (тот не узнаёт о том, что задачу закрыли
    или поменяли напрямую в ClickUp, минуя бота). Возвращает список словарей
    {"id", "name", "priority" (urgent/high/normal/low/None), "date_created" (unix-время
    в секундах), "url"}, по возрастанию даты создания. Бросает исключение при ошибке
    сети/API — вызывающий код сам решает, как это залогировать и что ответить
    пользователю."""
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
        batch = data.get("tasks") or []
        for t in batch:
            priority_field = t.get("priority") or {}
            priority = (priority_field.get("priority") or "").lower() or None
            try:
                created = float(t.get("date_created") or 0) / 1000
            except (TypeError, ValueError):
                created = 0.0
            tasks.append(
                {
                    "id": t.get("id"),
                    "name": t.get("name") or "(без названия)",
                    "priority": priority,
                    "date_created": created,
                    "url": t.get("url"),
                }
            )
        if data.get("last_page", True) or not batch:
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
