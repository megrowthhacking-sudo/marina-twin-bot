"""
Извлечение данных встречи из личного сообщения владелицы Marina Twin — отдельный
лёгкий вызов Claude (как task_extractor.py), без базы знаний: определяет, похоже ли
сообщение на просьбу поставить/записать встречу, и если да — вытаскивает название,
дату/время начала и окончания (ISO 8601 с таймзоной) и опционально место. Используется
из bot.py::_propose_meeting_draft — сама постановка в Google Calendar (calendar_client.py)
происходит только после подтверждения владелицей кнопкой, здесь только разбор текста.
"""

import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import config
from claude_client import client

logger = logging.getLogger(__name__)

_WEEKDAY_NAMES = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]

_SYSTEM_PROMPT_TEMPLATE = """Ты помогаешь понять, просит ли пользователь поставить/записать встречу \
в календарь, и если да — извлечь для неё данные.

Сегодня: {today} ({weekday}), часовой пояс {tz_name} (используй его как смещение для всех дат — \
например для Europe/Moscow это +03:00).

Правила:
- Если сообщение НЕ похоже на просьбу поставить встречу (обычный вопрос, задача, болтовня, \
уже прошедшая встреча в рассказе о том, что было) — верни {{"is_meeting": false}}.
- Если похоже, но не хватает данных даже приблизительно понять дату/время — тоже верни \
{{"is_meeting": false}}, лучше пропустить, чем выдумать дату.
- "start" и "end" — ISO 8601 datetime С УКАЗАНИЕМ ТАЙМЗОНЫ (например "2026-09-08T15:00:00+03:00"). \
Если длительность не указана явно в сообщении — считай встречу часовой (end = start + 1 час).
- "title" — короткое название встречи по сути (до ~80 символов), без даты/времени внутри названия.
- "location" — место или ссылка на созвон, если явно упомянуты в сообщении, иначе пустая строка "".

Ответь СТРОГО валидным JSON без markdown-разметки и без пояснений вокруг, в формате:
{{"is_meeting": true, "title": "...", "start": "...", "end": "...", "location": "..."}}
или {{"is_meeting": false}}"""


def extract_meeting(text: str, tz_name: str | None = None) -> dict | None:
    """Возвращает {"title", "start", "end", "location"}, если сообщение похоже на просьбу
    поставить встречу, иначе None (в т.ч. если Claude вернул невалидный/неполный JSON —
    лучше промолчать, чем предложить ошибочный черновик)."""
    tz_name = tz_name or config.MARINATWIN_TIMEZONE
    now = datetime.now(ZoneInfo(tz_name))
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        today=now.strftime("%Y-%m-%d %H:%M"),
        weekday=_WEEKDAY_NAMES[now.weekday()],
        tz_name=tz_name,
    )

    response = client.messages.create(
        model=config.LIGHT_MODEL_NAME,
        max_tokens=512,
        system=system_prompt,
        messages=[{"role": "user", "content": text}],
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
        logger.warning("Не удалось распарсить JSON от meeting_extractor, сырой ответ: %s", raw[:500])
        return None

    if not parsed.get("is_meeting"):
        return None

    title = (parsed.get("title") or "").strip()
    start = (parsed.get("start") or "").strip()
    end = (parsed.get("end") or "").strip()
    if not title or not start or not end:
        return None

    # Валидируем, что start/end реально парсятся как ISO datetime с таймзоной — иначе
    # calendar_client.create_event упадёт на этапе вызова Google API, а не здесь, где
    # проще молча отказаться от черновика и попросить сформулировать точнее.
    try:
        parsed_start = datetime.fromisoformat(start)
        datetime.fromisoformat(end)
    except ValueError:
        logger.warning("meeting_extractor вернул невалидные даты: start=%r end=%r", start, end)
        return None
    if parsed_start.tzinfo is None:
        logger.warning("meeting_extractor вернул дату без таймзоны: %r", start)
        return None

    return {
        "title": title,
        "start": start,
        "end": end,
        "location": (parsed.get("location") or "").strip(),
    }
