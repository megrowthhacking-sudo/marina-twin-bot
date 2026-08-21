"""
Тонкий клиент над ClickUp API v2 — создание задач.
Авторизация — личный токен в заголовке Authorization (без "Bearer").
Документация: https://developer.clickup.com/reference/createtask
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


def create_task(name: str, description: str = "", priority: str | None = None) -> dict:
    """Создаёт задачу в списке config.CLICKUP_LIST_ID. Бросает исключение при ошибке —
    вызывающий код (bot.py) сам решает, как это залогировать и не уронить остальную выгрузку."""
    if not config.CLICKUP_ENABLED:
        raise RuntimeError("ClickUp не настроен (нет CLICKUP_API_TOKEN или CLICKUP_LIST_ID)")

    payload: dict = {"name": name[:255], "description": description[:8000]}
    priority_num = PRIORITY_MAP.get((priority or "").lower())
    if priority_num:
        payload["priority"] = priority_num

    url = f"{BASE_URL}/list/{config.CLICKUP_LIST_ID}/task"
    resp = requests.post(url, headers=_headers(), json=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()


def test_connection() -> tuple[bool, str]:
    """Простая проверка токена/списка — дергает список, ничего не создавая.
    Удобно для ручной диагностики после деплоя (см. DEPLOY.md)."""
    if not config.CLICKUP_ENABLED:
        return False, "CLICKUP_API_TOKEN или CLICKUP_LIST_ID не заданы"
    try:
        resp = requests.get(
            f"{BASE_URL}/list/{config.CLICKUP_LIST_ID}",
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
