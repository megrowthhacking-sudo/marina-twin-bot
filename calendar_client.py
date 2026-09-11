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
from datetime import datetime, timedelta

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


def _find_duplicate_event(title: str, start_iso: str, end_iso: str) -> str | None:
    """Ищет в личном календаре Марины (config.GOOGLE_CALENDAR_ID) уже существующее
    событие с тем же названием (без учёта регистра) в окне времени [start_iso - 30мин,
    end_iso + 30мин] — используется create_event(), чтобы повторное нажатие кнопки
    подтверждения встречи (см. bot.py::handle_calendar_callback) или ретрай не создавали
    несколько одинаковых событий. Возвращает id найденного события или None, если
    дубликат не найден. Любая ошибка поиска (сеть/API) не должна мешать созданию
    события — в этом случае просто логируем и возвращаем None."""
    try:
        service = _get_service()
        start_dt = datetime.fromisoformat(start_iso)
        end_dt = datetime.fromisoformat(end_iso)
        time_min = (start_dt - timedelta(minutes=30)).isoformat()
        time_max = (end_dt + timedelta(minutes=30)).isoformat()
        result = (
            service.events()
            .list(
                calendarId=config.GOOGLE_CALENDAR_ID,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
            )
            .execute()
        )
        for item in result.get("items", []):
            if item.get("summary", "").strip().lower() == title.strip().lower():
                return item["id"]
        return None
    except Exception as e:
        logger.warning("Ошибка поиска дублей события '%s': %s", title, e)
        return None


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
    existing_id = _find_duplicate_event(title, start_iso, end_iso)
    if existing_id is not None:
        logger.info("Найден дубликат события '%s' (id=%s), новое событие не создаётся", title, existing_id)
        return existing_id
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


def list_events(time_min_iso: str, time_max_iso: str) -> list[dict]:
    """Тянет события из личного календаря Марины (config.GOOGLE_CALENDAR_ID) за
    полуоткрытый интервал [time_min_iso, time_max_iso) — используется командой
    /calendar (см. bot.py::handle_calendar_view_callback) для показа списка событий
    за выбранный период (сегодня/завтра/неделя/месяц). Оба аргумента — ISO 8601
    datetime со смещением (см. bot.py::_calendar_period_bounds). singleEvents=True
    разворачивает повторяющиеся события в отдельные экземпляры, отсортированные по
    времени начала. Возвращает список словарей {"title", "start", "end", "location",
    "all_day"} — "start"/"end" остаются ISO-строками как их вернул Google (с таймзоной
    для обычных событий, только дата "YYYY-MM-DD" для событий на весь день, см.
    "all_day"). Читает ВСЕ события календаря за период, не только созданные ботом —
    это осознанно: команда задумана как полноценный обзор расписания, а не только
    зеркало собственных встреч бота. Бросает исключение при ошибке сети/API —
    вызывающий код сам решает, как это залогировать и что ответить."""
    service = _get_service()
    response = (
        service.events()
        .list(
            calendarId=config.GOOGLE_CALENDAR_ID,
            timeMin=time_min_iso,
            timeMax=time_max_iso,
            singleEvents=True,
            orderBy="startTime",
            maxResults=250,
        )
        .execute()
    )
    events = []
    for item in response.get("items", []):
        start = item.get("start", {})
        end = item.get("end", {})
        events.append(
            {
                "title": item.get("summary") or "(без названия)",
                "start": start.get("dateTime") or start.get("date"),
                "end": end.get("dateTime") or end.get("date"),
                "all_day": "dateTime" not in start,
                "location": item.get("location") or "",
            }
        )
    return events
