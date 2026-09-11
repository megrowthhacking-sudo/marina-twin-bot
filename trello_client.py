"""
Тонкий клиент над Trello REST API (v1) — только чтение, только то, что нужно для
напоминаний о расписании (см. schedule_reminders.py), по прямому запросу владелицы,
часть 42.
Авторизация — API key + token в query-параметрах. Доска "001 Личное расписание
Марина" (config.TRELLO_BOARD_ID) находится на ОТДЕЛЬНОМ Trello-аккаунте владелицы
(m@ecombank.io). Пока TRELLO_API_KEY/TRELLO_TOKEN/TRELLO_BOARD_ID не заданы —
config.TRELLO_ENABLED = False и этот модуль просто не вызывается.
Документация: https://developer.atlassian.com/cloud/trello/rest/
"""
import logging
import requests
import config

logger = logging.getLogger(__name__)

BASE_URL = "https://api.trello.com/1"

def _auth_params() -> dict:
 return {"key": config.TRELLO_API_KEY, "token": config.TRELLO_TOKEN}

def get_board_lists() -> list[dict]:
 resp = requests.get(
 f"{BASE_URL}/boards/{config.TRELLO_BOARD_ID}/lists",
 params={**_auth_params(), "fields": "id,name", "cards": "none"},
 timeout=20,
 )
 resp.raise_for_status()
 return [{"id": item.get("id"), "name": item.get("name") or ""} for item in resp.json()]

def find_list_id_by_name(name: str) -> str | None:
 target = name.strip().lower()
 for item in get_board_lists():
 if (item["name"] or "").strip().lower() == target:
 return item["id"]
 return None

def get_list_cards(list_id: str) -> list[dict]:
 resp = requests.get(
 f"{BASE_URL}/lists/{list_id}/cards",
 params={**_auth_params(), "fields": "id,name,due,url", "filter": "open"},
 timeout=20,
 )
 resp.raise_for_status()
 return [
 {
 "id": item.get("id"),
 "name": item.get("name") or "(без названия)",
 "due": item.get("due"),
 "url": item.get("url"),
 }
 for item in resp.json()
 ]

def get_weekday_cards(weekday_name: str) -> list[dict]:
 list_id = find_list_id_by_name(weekday_name)
 if list_id is None:
 logger.warning("Trello: не нашла список с именем «%s» на доске %s", weekday_name, config.TRELLO_BOARD_ID)
 return []
 return get_list_cards(list_id)

def test_connection() -> tuple[bool, str]:
 if not config.TRELLO_ENABLED:
 return False, "Trello не настроен (нет TRELLO_API_KEY/TRELLO_TOKEN/TRELLO_BOARD_ID)"
 try:
 lists = get_board_lists()
 names = ", ".join(item["name"] for item in lists) or "(списков нет)"
 return True, f"Доска найдена, списки: {names}"
 except requests.HTTPError as e:
 return False, f"Trello вернул ошибка: {e.response.status_code} {e.response.text[:200]}"
 except Exception as e:
 return False, f"Не удалось подключиться к Trello: {e}"
