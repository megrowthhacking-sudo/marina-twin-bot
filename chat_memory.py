"""
"Память" группового чата — по прямой просьбе владелицы (06.09): бот должен накапливать
и обновлять сжатую сводку того, что обсуждалось в каждой группе, и учитывать её при
предложении черновиков ответов Марине (см. escalation.draft_initial_answer, параметр
chat_summary), а не отвечать только на основе самого вопроса.

Источник сырых данных — уже существующая таблица storage.group_messages (она и так
копит каждое сообщение группы с момента, как бот начал в ней работать; ничего нового
здесь не логируется). Эта память — скользящая (rolling) сводка: periodic_memory_job
(bot.py) раз в config.MEMORY_UPDATE_INTERVAL_MINUTES обходит чаты с новыми сообщениями
и просит лёгкую модель (config.LIGHT_MODEL_NAME — без полной базы знаний и без голоса
Марины, как task_extractor.py/escalation.rephrase_answer) построить НОВУЮ полную сводку
на основе старой сводки + накопившихся с прошлого раза сообщений. Старая сводка при
этом не хранится отдельно по слоям — каждое обновление полностью заменяет предыдущую
(см. storage.save_chat_memory), поэтому важно, чтобы сама модель заботилась о том, чтобы
не терять из старой сводки то, что всё ещё актуально.

ВАЖНО — платформенное ограничение, а не недоработка кода: Telegram Bot API не даёт
боту доступа к сообщениям, отправленным ДО того, как его добавили в чат / до того как он
начал их получать. Эта память физически может опираться только на то, что бот увидел
сам, начиная с момента добавления в конкретный чат — "прочитать историю чата с самого
начала" в буквальном смысле (до появления бота) через Bot API невозможно.
"""

import logging

import config
import storage
from claude_client import client

logger = logging.getLogger(__name__)

# Сколько сообщений чата максимум пересказываем модели за одно обновление сводки —
# если новых сообщений накопилось больше (очень активный чат или бот долго не
# обновлял память), лишнее подхватится следующими прогонами periodic_memory_job, а не
# раздует один запрос до неоправданной длины/стоимости.
_MAX_MESSAGES_PER_UPDATE = 400

# Не даём самой сводке расти бесконечно с каждым обновлением — иначе через месяцы
# активного чата она станет непомерно длинной и дорогой на каждый последующий вызов.
_MAX_SUMMARY_CHARS = 2000

_SUMMARY_SYSTEM_PROMPT = f"""Ты ведёшь компактную "память" одного рабочего группового чата для
Марины — владелицы бизнеса. Тебе дают (1) предыдущую сводку того, что уже известно об этом
чате (может быть пустой, если это первое обновление), и (2) новые сообщения чата, которые
пришли с прошлого обновления.

Составь НОВУЮ полную сводку чата — объединение того, что осталось актуальным из старой
сводки, и того нового, что появилось в свежих сообщениях. Не пиши "дополнение" или "изменения
с прошлого раза" — нужен цельный самодостаточный текст, как будто ты пишешь его с нуля, зная
всё, что знала раньше, и всё новое.

Включай: кто по каким вопросам/проектам пишет в этом чате, какие решения были приняты, какие
вопросы остались открытыми/без ответа, какие договорённости или дедлайны упоминались, любой
контекст, который поможет позже составить уместный ответ от лица Марины в этом чате. Не
включай: бытовую болтовню и рутинные обновления статуса без содержания (если только это не
единственное, что было в чате).

Пиши по-русски, нейтрально и по существу, не более {_MAX_SUMMARY_CHARS} символов. Если
сообщений слишком много, чтобы уместить все детали — сохраняй самое важное для будущего
контекста, а не самое свежее по времени. Не выдумывай ничего, чего нет в предоставленном
тексте. Ответь только текстом сводки, без пояснений и без заголовков."""


def _format_messages(messages: list[dict]) -> str:
    lines = []
    for m in messages:
        text = (m.get("text") or "").strip()
        if not text:
            continue
        lines.append(f"{m.get('user_name') or 'кто-то'}: {text}")
    return "\n".join(lines)


def update_chat_memory(chat_id: int, chat_title: str) -> None:
    """Обновляет сводку памяти одного чата, если у него накопились новые сообщения с
    прошлого обновления (см. storage.get_chats_with_new_messages_for_memory,
    periodic_memory_job в bot.py). Лучшим усилием — при любой ошибке (сеть, лимиты
    Claude) просто логирует и ничего не сохраняет, чтобы курсор (last_message_id) не
    сдвинулся мимо необработанных сообщений: следующий тик job попробует снова с той же
    точки."""
    existing = storage.get_chat_memory(chat_id)
    since_id = existing["last_message_id"] if existing else 0
    previous_summary = existing["summary"] if existing else ""

    new_messages = storage.get_messages_since(chat_id, since_id, limit=_MAX_MESSAGES_PER_UPDATE)
    if not new_messages:
        return

    transcript = _format_messages(new_messages)
    if not transcript:
        # Сообщения были, но все пустые (техническое обычно не бывает, но не падаем) —
        # всё равно сдвигаем курсор, чтобы не пытаться пересчитать то же самое вечно.
        storage.save_chat_memory(chat_id, chat_title, previous_summary, new_messages[-1]["id"])
        return

    user_content = (
        f"Групповой чат: «{chat_title}»\n\n"
        f"Предыдущая сводка (пусто, если это первое обновление):\n{previous_summary or '(пусто)'}\n\n"
        f"Новые сообщения с прошлого обновления:\n{transcript}"
    )
    try:
        response = client.messages.create(
            model=config.LIGHT_MODEL_NAME,
            max_tokens=1024,
            system=_SUMMARY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        new_summary = "\n".join(block.text for block in response.content if block.type == "text").strip()
    except Exception:
        logger.exception("Не удалось обновить память чата %s («%s»)", chat_id, chat_title)
        return

    if not new_summary:
        logger.warning("Обновление памяти чата %s («%s») вернуло пустой текст — курсор не сдвигаю", chat_id, chat_title)
        return

    storage.save_chat_memory(chat_id, chat_title, new_summary[:_MAX_SUMMARY_CHARS], new_messages[-1]["id"])


def get_summary_for_draft(chat_id: int) -> str | None:
    """Текущая сводка памяти чата для подстановки в escalation.draft_initial_answer —
    None, если по этому чату памяти ещё нет (черновик составляется как раньше, без
    этого контекста)."""
    memory = storage.get_chat_memory(chat_id)
    if not memory or not memory["summary"]:
        return None
    return memory["summary"]
