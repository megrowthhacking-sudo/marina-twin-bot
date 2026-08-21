"""
Извлечение задач из накопленной переписки группового чата.

Это НЕ разговорная персона Marina Twin — отдельный, лёгкий вызов Claude без
загрузки полной базы знаний (это был бы дорогой и ненужный оверхед для
фонового job'а, который просто читает чат и вытаскивает поручения).
"""

import json
import logging

import config
from claude_client import client

logger = logging.getLogger(__name__)

# Короткий словарь внутренних терминов — чтобы экстрактор понимал контекст
# переписки (названия проектов/сущностей), не подгружая всю базу знаний.
_GLOSSARY = """
Контекст компании (коротко, чтобы понимать переписку):
- «Алтын» / «Кошелёк Алтын» — платёжный проект компании, юрисдикция РФ. Брокер Алтын, РНКО «Алтын» — свои юрлица/партнёры.
- ATLAS — второй проект компании, международный (юрлица в Гонконге и Канаде: ALTAS PAY LIMITED, ATLAS CARD LTD, ATLAS WALLET LTD).
- Речь часто идёт о подключении платёжных шлюзов, банков-партнёров, комплаенсе, KYC/AML, договорах, встречах с банками/партнёрами.
"""

_SYSTEM_PROMPT = f"""Ты читаешь переписку рабочего группового чата сотрудников компании и извлекаешь из неё
конкретные задачи — то, что кто-то поручил, пообещал сделать, или что явно требует действия.

{_GLOSSARY}

Правила:
- Извлекай только конкретные, действительно поручаемые задачи — не общие обсуждения, не риторические вопросы, не смолл-ток.
- Если задача уже явно закрыта в переписке ("сделано", "готово") — не включай её.
- Если из сообщения не ясно, что именно нужно сделать — пропусти, лучше пропустить, чем выдумать.
- Заголовок задачи — короткий, по сути (до ~80 символов). Описание — 1-3 предложения с контекстом и прямой цитатой источника.
- Если в переписке явно назван ответственный (по имени) — укажи его в описании как "Похоже, ответственный: <имя>" (это только предположение, не факт).
- Приоритет — "urgent"/"high"/"normal"/"low", по умолчанию "normal", "urgent"/"high" только если в переписке явно есть срочность/дедлайн/эскалация.

Ответь СТРОГО валидным JSON без markdown-разметки и без пояснений вокруг, в формате:
{{"tasks": [{{"title": "...", "description": "...", "priority": "normal"}}]}}

Если задач нет — верни {{"tasks": []}}."""


def extract_tasks(chat_title: str, messages: list[dict]) -> list[dict]:
    """messages — список {"user_name": str, "text": str, "ts": float} в хронологическом порядке."""
    if not messages:
        return []

    transcript_lines = [f"{m['user_name']}: {m['text']}" for m in messages]
    transcript = "\n".join(transcript_lines)

    user_content = f"Групповой чат: «{chat_title}»\n\nПереписка:\n{transcript}"

    response = client.messages.create(
        model=config.MODEL_NAME,
        max_tokens=2048,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    raw = "\n".join(block.text for block in response.content if block.type == "text").strip()
    # На случай если модель всё же обернула ответ в ```json ... ```
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
        tasks = parsed.get("tasks", [])
        if not isinstance(tasks, list):
            raise ValueError("tasks не список")
        return tasks
    except (json.JSONDecodeError, ValueError):
        logger.warning("Не удалось распарсить JSON от экстрактора задач, сырой ответ: %s", raw[:500])
        return []
