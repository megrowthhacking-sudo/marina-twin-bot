"""
Интеграция с Google Calendar — создание встреч по запросу владелицы из личного
диалога с Marina Twin (см. bot.py::_propose_meeting_draft / handle_calendar_callback).

Авторизация через сервисный аккаунт Google (config.GOOGLE_SERVICE_ACCOUNT_JSON),
которому Марина вручную даёт доступ "на изменение событий" к своему личному календарю
(config.GOOGLE_CALENDAR_ID, обычно её gmail-адрес — id основного календаря совпадает
с адресом почты) — без интерактивного OAuth-флоу и без истекающих пользовательских
токенов, что надёжнее для постоянно работающего сервера, чем OAuth user-consent.
"""

import json
import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build

import config

logger = logging.getLogger(__name__)

_SCOPES = ["https://www.googleapis.com/auth/calendar"]

_service = None


def _get_service():
    global _service
    if _service is None:
        info = json.loads(config.GOOGLE_SERVICE_ACCOUNT_JSON)
        creds = service_account.Credentials.from_service_account_info(info, scopes=_SCOPES)
        _service = build("calendar", "v3", credentials=creds, cache_discovery=False)
    return _service


def create_event(
    title: str,
    start_iso: str,
    end_iso: str,
    location: str | None = None,
    description: str | None = None,
) -> str:
    """Создаёт событие в личном календаре Марины (config.GOOGLE_CALENDAR_ID).
    start_iso/end_iso — ISO 8601 datetime С таймзоной (см. meeting_extractor.py — Claude
    сам подставляет смещение по config.MARINATWIN_TIMEZONE, здесь просто передаём как
    есть). Возвращает id созданного события в Google Calendar — пока используется только
    для лога/будущего редактирования, отдельно нигде не хранится за пределами
    storage.pending_meetings.calendar_event_id."""
    service = _get_service()
    body = {
        "summary": title,
        "start": {"dateTime": start_iso},
        "end": {"dateTime": end_iso},
        # По просьбе владелицы (06.09): календарь m@altyn.one — рабочий, и на него могут
        # быть заведены другие люди с доступом на просмотр. "private" — штатное поле
        # Google Calendar API: коллеги с доступом "See all event details" видят такое
        # событие только как "занято", без названия/описания/места — детали видит только
        # организатор (сервисный аккаунт) и сама Марина через свой аккаунт-владелец
        # календаря. Это не настройка ACL, а свойство конкретного события — применяется
        # ко всем встречам, которые ставит бот, без исключений.
        "visibility": "private",
    }
    if location:
        body["location"] = location
    if description:
        body["description"] = description
    event = service.events().insert(calendarId=config.GOOGLE_CALENDAR_ID, body=body).execute()
    logger.info("Событие создано в Google Calendar: %s (%s)", title, event.get("id"))
    return event["id"]
