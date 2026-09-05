"""
Пересказ ответа Марины на вопрос коллеги из группового чата — отдельный лёгкий
вызов Claude, без загрузки полной базы знаний (как и task_extractor.py). Нужен,
чтобы превратить короткий/неформальный ответ владелицы в личке в связное сообщение
от её имени, которое затем публикуется в исходном групповом чате — так, будто она
ответила туда сама.
"""

import logging

import claude_client
import clickup_client
import config
import kb
from claude_client import client

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """Ты помогаешь Марине быстро отвечать коллегам в рабочих групповых чатах.

Тебе дают вопрос коллеги из группового чата и черновой ответ Марины на него (черновой ответ
может быть коротким, неформальным, с опечатками — это нормально, это просто её быстрый ответ
в личных сообщениях).

Перефразируй ответ Марины в связное, дружелюбное сообщение для группового чата — от её лица,
в деловом, но живом тоне, как будто она сама печатает в чат прямо сейчас. Сохраняй суть и все
факты из её ответа, ничего не добавляй от себя и не выдумывай деталей, которых в её ответе не
было. Если её ответ уже сам по себе хорошо сформулирован — просто слегка пригладь стиль, не
переписывай кардинально.

Ответь только текстом сообщения для чата, без пояснений, без кавычек вокруг и без подписи."""


def rephrase_answer(group_title: str, asker_name: str, question: str, raw_answer: str) -> str:
    user_content = (
        f"Групповой чат: «{group_title}»\n"
        f"Вопрос от {asker_name}: {question}\n\n"
        f"Черновой ответ Марины: {raw_answer}"
    )
    response = client.messages.create(
        model=config.LIGHT_MODEL_NAME,
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    text = "\n".join(block.text for block in response.content if block.type == "text").strip()
    return text or raw_answer


_INITIAL_DRAFT_SYSTEM_PROMPT = """Ты помогаешь Марине быстро отвечать коллегам в рабочих групповых чатах.
Тебе дают вопрос коллеги из группового чата, адресованный Марине. Составь короткий,
дружелюбный черновик ответа от её лица, в деловом, но живом тоне — как будто она сама
печатает в чат прямо сейчас.
У тебя есть доступ к базе знаний компании (право, регламенты, детали проектов Atlas и
Altyn), к списку открытых задач ClickUp по проекту этого чата (если он приложен ниже, в
сообщении пользователя) и к веб-поиску для публичных, проверяемых в интернете фактов
(курсы, цены, законы, требования банков/регуляторов). Используй всё это перед ответом, а
не угадывай.
ВАЖНО: даже так у тебя нет доступа к самым последним договорённостям, которые ещё нигде
не отражены — ни в базе, ни в задачах ClickUp, ни в интернете. Не выдумывай факты, даты,
цифры или решения, которых нет ни в вопросе, ни в базе, ни в задачах, ни в результатах
поиска. Если вопрос всё равно требует конкретики, которой у тебя нет, честно предложи
нейтральный ответ-заглушку (например, что она уточнит и вернётся), а не выдумывай
детали. Никогда не утверждай, что уже что-то сделано (закрыла задачу, переименовала,
отправила файл и т.п.) — ты не выполняешь реальных действий, только предлагаешь текст.
Марина сама решит, отправлять этот черновик, попросить другой вариант или ответить
по-своему.
Ответь только текстом чернового сообщения для чата, без пояснений, без кавычек вокруг и
без подписи."""


def draft_initial_answer(
    group_title: str, asker_name: str, question: str, project_key: str | None = None
) -> str:
    """Первый черновик ответа на вопрос из группы — бот предлагает его сразу, ещё до
    того как Марина написала хоть слово (см. _propose_initial_draft в bot.py). Подключает
    базу знаний Marina Twin (тот же core, что и в личных диалогах — Atlas и Altyn уже
    часть core, страновые модули СНГ подключаются по упоминанию в самом вопросе через
    kb.detect_countries) и, если чат закреплён за проектом (project_key), список открытых
    задач этого проекта из ClickUp — для контекста, не как источник истины. ClickUp
    читается лучшим усилием: если не получилось (нет токена, сеть, список не настроен) —
    просто продолжаем без этого контекста, не роняем весь черновик. Пустая строка, если
    Claude не вернул текст — вызывающий код в этом случае переходит сразу к "напиши сама"."""
    active_countries = sorted(kb.detect_countries(question))[: kb.MAX_ACTIVE_COUNTRIES]
    system_blocks = claude_client.build_system_blocks(active_countries) + [
        {"type": "text", "text": _INITIAL_DRAFT_SYSTEM_PROMPT}
    ]
    tasks_context = ""
    if project_key:
        list_id = config.CLICKUP_LIST_IDS.get(project_key)
        if list_id:
            try:
                open_tasks = clickup_client.get_open_tasks(list_id)
            except Exception:
                logger.exception(
                    "Не удалось прочитать задачи ClickUp для черновика ответа (проект %s)", project_key
                )
                open_tasks = []
            if open_tasks:
                lines = "\n".join(f"- {t['name']}" for t in open_tasks[:20])
                tasks_context = (
                    f"\n\nОткрытые задачи проекта в ClickUp (для справки, не факт что все "
                    f"относятся к вопросу):\n{lines}"
                )
    user_content = f"Групповой чат: «{group_title}»\nВопрос от {asker_name}: {question}{tasks_context}"
    response = client.messages.create(
        model=config.MODEL_NAME,
        max_tokens=1024,
        system=system_blocks,
        messages=[{"role": "user", "content": user_content}],
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
    )
    return "\n".join(block.text for block in response.content if block.type == "text").strip()


_CORRECTION_SYSTEM_PROMPT = """Ты помогаешь Марине быстро отвечать коллегам в рабочих групповых чатах. Тебе дают вопрос коллеги из группового чата, ответ, который Марина уже отправляла туда ранее, и её новую правку или дополнение. Перефразируй правку Марины в связное, дружелюбное сообщение-уточнение для группового чата — от её лица. Сохраняй суть и все факты из её правки, ничего не добавляй от себя. Не пересказывай заново предыдущий ответ целиком — это именно уточнение/дополнение к нему. Ответь только текстом сообщения для чата, без пояснений, без кавычек вокруг и без подписи."""


def rephrase_correction(group_title: str, asker_name: str, question: str, previous_answer: str, raw_correction: str) -> str:
    user_content = (
        f"Групповой чат: «{group_title}»\n"
        f"Вопрос от {asker_name}: {question}\n\n"
        f"Ранее отвечала: {previous_answer}\n\n"
        f"Новая правка Марины: {raw_correction}"
    )
    response = client.messages.create(
        model=config.LIGHT_MODEL_NAME,
        max_tokens=1024,
        system=_CORRECTION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    text = "\n".join(block.text for block in response.content if block.type == "text").strip()
    return text or raw_correction
