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
from datetime import datetime, timedelta
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


# --- Обратное направление: ClickUp-задача → авто-встреча в Google Calendar ---
#
# extract_meeting_from_task ниже — по прямой просьбе владелицы (23.09.2026): в отличие от
# extract_meeting выше (источник — личное сообщение владелицы в диалоге с Twin, результат
# только ПРЕДЛАГАЕТСЯ и требует подтверждения кнопкой "✅ Применить", см.
# bot.py::_propose_meeting_draft/handle_calendar_callback), здесь источник — ЛЮБАЯ задача,
# заведённая КЕМ УГОДНО в ClickUp workspace (не только 4 официальных проектных списка, а
# по всему workspace, включая WEEKLY TASKS — см. clickup_meeting_watch.py и
# clickup_client.get_open_tasks_team_wide), а результат используется для СРАЗУ ЖЕ
# автоматического создания события в Google Calendar, БЕЗ каких-либо кнопок
# подтверждения — владелице только пост-фактум приходит уведомление о заведённой
# встрече, чтобы она могла поправить её, если разбор текста ошибся.
#
# Поэтому и стратегия отличается: extract_meeting сознательно предпочитает вернуть None
# при малейшей неопределённости ("лучше пропустить, чем выдумать дату") — там всё равно
# есть черновик с подтверждением, спешить рискованно не нужно. extract_meeting_from_task
# наоборот — если Claude решил, что текст ПОХОЖ на встречу/созвон/звонок, но точное время
# не названо явно в тексте, функция всё равно возвращает результат, а не None: время
# берётся из поля due_date задачи (если оно есть), а если и due_date нет — из created_date
# задачи, всегда на 12:00 по местной таймзоне. В обоих случаях результат помечается
# "time_is_guessed": true — вызывающий код (clickup_meeting_watch.py) обязан включить эту
# пометку в пост-фактум уведомление владелице, чтобы было явно понятно, что время могло
# быть угадано неверно. Если же сам текст вообще не похож на встречу/созвон/звонок (обычная
# рабочая задача без созвона) — возвращается None, как и раньше.

_TASK_SYSTEM_PROMPT_TEMPLATE = """Ты анализируешь задачу из ClickUp (общий рабочий workspace компании) и решаешь, \
описывает ли она встречу, созвон, звонок или другую синхронизацию людей в реальном времени — \
такую, которую стоит поставить как событие в календарь.

Сегодня: {today} ({weekday}), часовой пояс {tz_name} (используй его как смещение для всех дат — \
например для Europe/Moscow это +03:00).

Тебе даны поля задачи ClickUp:
- Название: {title}
- Описание: {description}
- Дедлайн (due_date), если задан: {due_date}
- Дата создания задачи (created_date): {created_date}

Правила:
- Если задача явно НЕ про встречу/созвон/звонок (обычная рабочая задача, документ, напоминание \
без участия других людей в реальном времени) — верни {{"is_meeting": false}}.
- Если задача ПОХОЖА на встречу/созвон/звонок (в названии или описании упоминается встреча, \
созвон, звонок, sync, call, meeting, собрание, переговоры и т.п.) — верни результат, даже если \
точное время нигде явно не названо. В таком случае:
  - если в тексте есть явное время (например "в 15:00", "завтра в 10 утра") — используй его \
и поставь "time_is_guessed": false;
  - если явного времени в тексте нет, но задан due_date — используй due_date как время начала \
и поставь "time_is_guessed": true;
  - если явного времени нет и due_date не задан — используй created_date, время 12:00 по \
часовому поясу {tz_name}, и поставь "time_is_guessed": true.
- "start" и "end" — ISO 8601 datetime С УКАЗАНИЕМ ТАЙМЗОНЫ (например "2026-09-08T15:00:00+03:00"). \
Если длительность не указана явно в тексте — считай встречу часовой (end = start + 1 час).
- "title" — короткое название встречи по сути (до ~80 символов), без даты/времени внутри названия.
- "location" — место или ссылка на созвон, если явно упомянуты в названии/описании, иначе пустая \
строка "".

Ответь СТРОГО валидным JSON без markdown-разметки и без пояснений вокруг, в формате:
{{"is_meeting": true, "title": "...", "start": "...", "end": "...", "location": "...", \
"time_is_guessed": false}}
или {{"is_meeting": false}}"""


def extract_meeting_from_task(
    title: str,
    description: str = "",
    due_date_iso: str | None = None,
    created_iso: str | None = None,
    tz_name: str | None = None,
) -> dict | None:
    """Возвращает {"title", "start", "end", "location", "time_is_guessed"}, если задача
    ClickUp похожа на встречу/созвон/звонок, иначе None. В отличие от extract_meeting
    выше, сознательно НЕ отказывается от результата только из-за отсутствия явного
    времени в тексте — при нехватке данных время угадывается (см. модульный докстринг
    выше) и результат помечается "time_is_guessed": true, вместо молчаливого None.
    Используется clickup_meeting_watch.py для автоматической (без подтверждения)
    постановки события в Google Calendar по любой новой задаче ClickUp workspace."""
    tz_name = tz_name or config.MARINATWIN_TIMEZONE
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz)
    system_prompt = _TASK_SYSTEM_PROMPT_TEMPLATE.format(
        today=now.strftime("%Y-%m-%d %H:%M"),
        weekday=_WEEKDAY_NAMES[now.weekday()],
        tz_name=tz_name,
        title=title or "(без названия)",
        description=description or "(без описания)",
        due_date=due_date_iso or "не задан",
        created_date=created_iso or "неизвестна",
    )

    response = client.messages.create(
        model=config.LIGHT_MODEL_NAME,
        max_tokens=512,
        system=system_prompt,
        messages=[{"role": "user", "content": f"Название: {title}\n\nОписание: {description}"}],
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
        logger.warning("Не удалось распарсить JSON от extract_meeting_from_task, сырой ответ: %s", raw[:500])
        return None

    if not parsed.get("is_meeting"):
        return None

    result_title = (parsed.get("title") or title or "").strip()
    start = (parsed.get("start") or "").strip()
    end = (parsed.get("end") or "").strip()
    time_is_guessed = bool(parsed.get("time_is_guessed"))

    if not result_title:
        return None

    # Claude иногда всё равно не подставляет start/end, даже когда явно попросили угадать —
    # в этом случае угадываем сами на стороне кода, а не отказываемся от результата, раз
    # текст явно похож на встречу (см. докстринг модуля выше — здесь мы всегда стараемся
    # что-то вернуть, а не молчать).
    if not start:
        fallback_dt = None
        if due_date_iso:
            try:
                fallback_dt = datetime.fromisoformat(due_date_iso)
            except ValueError:
                fallback_dt = None
        if fallback_dt is None and created_iso:
            try:
                created_dt = datetime.fromisoformat(created_iso)
                fallback_dt = created_dt.replace(hour=12, minute=0, second=0, microsecond=0)
            except ValueError:
                fallback_dt = None
        if fallback_dt is None:
            fallback_dt = now.replace(hour=12, minute=0, second=0, microsecond=0)
        if fallback_dt.tzinfo is None:
            fallback_dt = fallback_dt.replace(tzinfo=tz)
        start = fallback_dt.isoformat()
        end = (fallback_dt + timedelta(hours=1)).isoformat()
        time_is_guessed = True
    if not end:
        try:
            end = (datetime.fromisoformat(start) + timedelta(hours=1)).isoformat()
        except ValueError:
            return None

    try:
        parsed_start = datetime.fromisoformat(start)
        datetime.fromisoformat(end)
    except ValueError:
        logger.warning("extract_meeting_from_task вернул невалидные даты: start=%r end=%r", start, end)
        return None
    if parsed_start.tzinfo is None:
        logger.warning("extract_meeting_from_task вернул дату без таймзоны: %r", start)
        return None

    return {
        "title": result_title,
        "start": start,
        "end": end,
        "location": (parsed.get("location") or "").strip(),
        "time_is_guessed": time_is_guessed,
    }
