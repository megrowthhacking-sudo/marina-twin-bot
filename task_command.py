"""
Явная постановка задачи в конкретный ClickUp-список/статус — по прямой просьбе владелицы
(06.09): "Поставь Свете задачу в WEEKLY в статус Понедельник с пометкой срочно отправить
презентацию MSB ...". Отдельный лёгкий вызов Claude (как meeting_extractor.py/
task_extractor.py), без базы знаний: определяет, является ли сообщение владелицы В ЛИЧКЕ
БОТУ именно такой осознанной командой (а не обычным рабочим сообщением, которое и так
тихо заносится в ClickUp фоново — см. bot.py::_log_owner_dm_tasks), и если да — извлекает
ответственного, названное пространство/список, статус, приоритет и суть задачи.

Ключевое отличие от обычного фонового логирования: здесь ОБЯЗАТЕЛЬНО явно назван
список/пространство ("в WEEKLY", "в Атлас", "в список Расписание") — то, что делает эту
команду осознанной постановкой, а не просто рабочей репликой. Само сопоставление
названия с реальным config.CLICKUP_TASK_TARGETS и проверка статуса по реальному ClickUp
происходит уже в bot.py (_resolve_task_target/_resolve_task_status) — здесь только разбор
текста в сыром виде.
"""

import json
import logging

import config
from claude_client import client

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """Ты помогаешь понять, является ли личное сообщение владелицы боту ОСОЗНАННОЙ,
явной командой поставить ОДНУ конкретную задачу в конкретный ClickUp-список (пространство/проект),
и если да — извлечь для неё данные.

Это НЕ то же самое, что обычное рабочее сообщение о задаче (просто "надо сделать то-то") — такие
сообщения обрабатываются отдельно, автоматически, без явного разбора списка. Твоя задача — отличить
именно ЯВНУЮ команду постановки, у которой есть явно названное пространство/список (например
"в WEEKLY", "в Атлас", "в список Алтын", "в Расписание") — без этого признака верни
{"is_command": false}, даже если сообщение похоже на задачу.

Правила:
- "is_command": true ТОЛЬКО если в сообщении явно (1) звучит как команда поставить/добавить/завести
задачу (глаголы вроде "поставь", "добавь", "заведи задачу", "закинь задачу") И (2) явно назван
конкретный список/пространство ClickUp, куда её положить. Если хотя бы одно из двух не выполнено —
{"is_command": false} (обычное сообщение, не эта команда).
- "assignee_name" — имя ответственного, как оно прозвучало (например "Свете" → "Света"), в
именительном падеже, если это возможно понять по контексту; если ответственный не назван —
пустая строка "".
- "target_name" — как именно назван список/пространство в сообщении, ДОСЛОВНО (например "WEEKLY",
"Атлас", "Расписание") — не переводи и не подбирай синоним, дальнейшее сопоставление с реальными
списками ClickUp происходит отдельно.
- "status_name" — как назван статус, если он явно назван (например "Понедельник", "на согласовании");
если статус не назван — пустая строка "".
- "priority" — "urgent"/"high"/"normal"/"low", по умолчанию "normal"; "urgent" если явно есть слова
вроде "срочно"/"срочная"/"пометка срочно".
- "title" — короткая суть задачи (до ~120 символов), без служебных слов про список/статус/срочность.
- "description" — при необходимости, доп. детали задачи текстом (можно оставить как есть из сообщения,
без служебных слов про список/статус/срочность); если ничего сверх заголовка нет — пустая строка "".

Ответь СТРОГО валидным JSON без markdown-разметки и без пояснений вокруг, в формате:
{"is_command": true, "assignee_name": "...", "target_name": "...", "status_name": "...",
"priority": "normal", "title": "...", "description": "..."}
или {"is_command": false}"""


def extract_task_command(text: str) -> dict | None:
    """Возвращает {"assignee_name", "target_name", "status_name", "priority", "title",
    "description"}, если сообщение похоже на явную команду поставить задачу в конкретный
    список, иначе None (в т.ч. если Claude вернул невалидный/неполный JSON или явно
    назвал is_command=false — лучше промолчать и отдать сообщение обычной обработке
    _log_owner_dm_tasks, чем ошибочно распознать команду там, где её нет)."""
    response = client.messages.create(
        model=config.LIGHT_MODEL_NAME,
        max_tokens=512,
        system=_SYSTEM_PROMPT,
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
        logger.warning("Не удалось распарсить JSON от task_command, сырой ответ: %s", raw[:500])
        return None

    if not parsed.get("is_command"):
        return None

    title = (parsed.get("title") or "").strip()
    target_name = (parsed.get("target_name") or "").strip()
    if not title or not target_name:
        return None

    return {
        "assignee_name": (parsed.get("assignee_name") or "").strip(),
        "target_name": target_name,
        "status_name": (parsed.get("status_name") or "").strip(),
        "priority": (parsed.get("priority") or "normal").strip().lower(),
        "title": title,
        "description": (parsed.get("description") or "").strip(),
    }
