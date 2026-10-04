"""Сводки по групповым чатам и вопросы к их истории (03.10.2026, по прямой просьбе владелицы).
Telegram не даёт боту читать историю группы до его добавления, поэтому бот копит всё сам:
таблица group_messages (storage.py) хранит каждое сообщение групп и никогда не чистится.
Что делает модуль:
1) Когда бота добавляют в новую группу, он пишет владелице в личку, а когда в группе
   накопится SUMMARY_AFTER сообщений, один раз присылает краткую сводку, о чём чат.
2) Команда /chat (только владелица, только личка): выбор группы кнопками, затем кнопка
   "Кратко о чате" или любой вопрос текстом: ответ строится только по накопленной переписке.
   Режим держится MODE_TTL секунд после последнего вопроса или до кнопки "Закончить".
Модуль отдельный, потому что bot.py запускается как __main__; bot.py вызывает register(app),
on_group_message(...) и maybe_answer(...)."""
import asyncio
import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ChatMemberHandler, CommandHandler, ContextTypes
import config
import storage
logger = logging.getLogger("marina_twin_bot")
ACTIVE_KEY = "chd_active"
SUMMARY_AFTER = 30
MODE_TTL = 1800
MAX_CONTEXT_CHARS = 60000
MAX_FETCH = 3000
MSG_LIMIT = 3900
_SUMMARY_SYSTEM = (
    "Ты помогаешь владелице быстро понять, о чём рабочий Telegram-чат. По переписке ниже дай "
    "краткую сводку на русском, не больше 8 коротких строк: о чём чат и чей он, кто основные "
    "участники и их роли, главные темы и принятые решения, открытые вопросы и задачи. "
    "Опирайся только на переписку, ничего не выдумывай."
)
_QA_SYSTEM = (
    "Ты отвечаешь владелице на вопрос по переписке Telegram-чата. Отвечай по-русски, коротко и "
    "по делу, ТОЛЬКО на основе переписки ниже (и краткой сводки более старой части, если она "
    "есть). Если в данных ответа нет, так и скажи, не придумывай. Где уместно, называй даты и "
    "кто что сказал."
)
def init_db() -> None:
    storage._conn.execute(
        "CREATE TABLE IF NOT EXISTS chat_digest_state ("
        "chat_id INTEGER PRIMARY KEY, title TEXT, joined_at REAL NOT NULL, summarized INTEGER NOT NULL DEFAULT 0)"
    )
    storage._conn.commit()
def _is_owner(user) -> bool:
    return user is not None and config.OWNER_USER_ID is not None and user.id == config.OWNER_USER_ID
def _chunks(text: str) -> list[str]:
    out = []
    while len(text) > MSG_LIMIT:
        cut = text.rfind("\n", 0, MSG_LIMIT)
        cut = cut if cut > 0 else MSG_LIMIT
        out.append(text[:cut])
        text = text[cut:].lstrip("\n")
    out.append(text)
    return out
async def _send(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, reply_markup=None) -> None:
    parts = _chunks(text)
    for i, part in enumerate(parts):
        await context.bot.send_message(
            chat_id=chat_id, text=part, reply_markup=reply_markup if i == len(parts) - 1 else None
        )
def _load_messages(chat_id: int) -> tuple[str, int, int]:
    """Переписка чата одним текстом (новейшие сообщения важнее: при нехватке места
    отбрасываем самые старые). Возвращает (текст, сколько сообщений вошло, всего в журнале)."""
    rows = storage._conn.execute(
        "SELECT user_name, text, ts FROM group_messages WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
        (chat_id, MAX_FETCH),
    ).fetchall()
    total = storage._conn.execute("SELECT COUNT(*) FROM group_messages WHERE chat_id = ?", (chat_id,)).fetchone()[0]
    tz = ZoneInfo(config.MARINATWIN_TIMEZONE)
    lines: list[str] = []
    size = 0
    for name, text, ts in rows:
        line = f"{datetime.fromtimestamp(ts, tz).strftime('%d.%m %H:%M')} {name or '?'}: {text}"
        if size + len(line) > MAX_CONTEXT_CHARS:
            break
        lines.append(line)
        size += len(line) + 1
    lines.reverse()
    return "\n".join(lines), len(lines), total
def _ask_llm(system: str, user_text: str, model: str, max_tokens: int) -> str:
    from claude_client import client  # локальный импорт: тесты подменяют модуль
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_text}],
    )
    return "\n".join(b.text for b in response.content if b.type == "text").strip()


async def summarize_chat(chat_id: int, title: str) -> str:
    body, used, total = _load_messages(chat_id)
    if not body:
        return "В этом чате у меня пока нет сообщений."
    header = f"Чат: {title}\nСообщений в журнале: {total}, в сводку вошло последних: {used}.\n\n"
    return await asyncio.to_thread(_ask_llm, _SUMMARY_SYSTEM, header + body, config.LIGHT_MODEL_NAME, 700)
async def answer_question(chat_id: int, title: str, question: str) -> str:
    body, used, total = _load_messages(chat_id)
    if not body:
        return "В этом чате у меня пока нет сообщений, отвечать не по чему."
    older = ""
    memory = storage.get_chat_memory(chat_id)
    if memory and memory.get("summary"):
        older = f"Краткая сводка более старой части чата:\n{memory['summary']}\n\n"
    header = f"Чат: {title}\nСообщений в журнале: {total}, ниже последних: {used}.\n\n{older}Переписка:\n"
    user_text = f"{header}{body}\n\nВопрос владелицы: {question}"
    return await asyncio.to_thread(_ask_llm, _QA_SYSTEM, user_text, config.MODEL_NAME, 1200)


async def on_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Бота добавили в группу: запоминаем момент и сообщаем владелице в личку."""
    event = update.my_chat_member
    if event is None or event.chat.type not in ("group", "supergroup"):
        return
    was_in = event.old_chat_member.status in ("member", "administrator", "creator")
    now_in = event.new_chat_member.status in ("member", "administrator", "creator")
    if was_in or not now_in:
        return
    title = event.chat.title or str(event.chat.id)
    storage._conn.execute(
        "INSERT INTO chat_digest_state (chat_id, title, joined_at, summarized) VALUES (?, ?, ?, 0) "
        "ON CONFLICT(chat_id) DO UPDATE SET title = excluded.title, joined_at = excluded.joined_at, summarized = 0",
        (event.chat.id, title, time.time()),
    )
    storage._conn.commit()
    if config.OWNER_USER_ID is None:
        return
    try:
        await _send(
            context,
            config.OWNER_USER_ID,
            f"Меня добавили в группу «{title}». Читать историю до добавления я не могу, "
            f"поэтому коплю сообщения сам. Когда наберётся {SUMMARY_AFTER} сообщений, пришлю краткую сводку, "
            "о чём чат. Спросить о чате можно командой /chat.",
        )
    except Exception:
        logger.exception("chat_digest: не удалось уведомить владелицу о новой группе %s", event.chat.id)


async def on_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Сообщение в группе: когда после добавления бота накопилось SUMMARY_AFTER сообщений,
    один раз присылаем владелице краткую сводку чата."""
    chat = update.effective_chat
    if chat is None or chat.type not in ("group", "supergroup") or config.OWNER_USER_ID is None:
        return
    state = storage._conn.execute(
        "SELECT title, joined_at, summarized FROM chat_digest_state WHERE chat_id = ?", (chat.id,)
    ).fetchone()
    if state is None or state[2]:
        return
    title, joined_at = state[0] or chat.title or str(chat.id), state[1]
    count = storage._conn.execute(
        "SELECT COUNT(*) FROM group_messages WHERE chat_id = ? AND ts >= ?", (chat.id, joined_at)
    ).fetchone()[0]
    if count < SUMMARY_AFTER:
        return
    claimed = storage._conn.execute(
        "UPDATE chat_digest_state SET summarized = 1 WHERE chat_id = ? AND summarized = 0", (chat.id,)
    )
    storage._conn.commit()
    if claimed.rowcount == 0:
        return
    try:
        summary = await summarize_chat(chat.id, title)
        await _send(context, config.OWNER_USER_ID, f"Сводка по чату «{title}» (набралось {count} сообщений):\n\n{summary}")
    except Exception:
        logger.exception("chat_digest: не удалось отправить сводку по чату %s", chat.id)
        storage._conn.execute("UPDATE chat_digest_state SET summarized = 0 WHERE chat_id = ?", (chat.id,))
        storage._conn.commit()


async def on_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Бота добавили в группу (или вернули после удаления): запоминаем момент и пишем
    владелице в личку. Историю до этого момента Telegram боту не отдаёт."""
    change = update.my_chat_member
    if change is None or change.chat.type not in ("group", "supergroup"):
        return
    if change.new_chat_member.status not in ("member", "administrator"):
        return
    if change.old_chat_member.status not in ("left", "kicked"):
        return
    chat = change.chat
    title = chat.title or str(chat.id)
    storage._conn.execute(
        "INSERT OR REPLACE INTO chat_digest_state (chat_id, title, joined_at, summarized) VALUES (?, ?, ?, 0)",
        (chat.id, title, time.time()),
    )
    storage._conn.commit()
    storage.note_group_chat_seen(chat.id, title)
    if config.OWNER_USER_ID is None:
        return
    await context.bot.send_message(
        chat_id=config.OWNER_USER_ID,
        text=(
            f"Меня добавили в группу «{title}». Историю до добавления Telegram боту не показывает, "
            f"поэтому я копил переписку с этого момента. Когда накопится {SUMMARY_AFTER} сообщений, "
            "пришлю краткую сводку о чате. Спросить что-то по чату можно командой /chat."
        ),
    )


async def on_group_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, title: str) -> None:
    """Вызывается из bot.py после записи сообщения группы в журнал. Для недавно
    добавленной группы, когда накопилось SUMMARY_AFTER сообщений, один раз присылает
    владелице сводку. Для остальных групп ничего не делает."""
    if config.OWNER_USER_ID is None:
        return
    row = storage._conn.execute(
        "SELECT joined_at, summarized FROM chat_digest_state WHERE chat_id = ?", (chat_id,)
    ).fetchone()
    if not row or row[1]:
        return
    count = storage._conn.execute(
        "SELECT COUNT(*) FROM group_messages WHERE chat_id = ? AND ts >= ?", (chat_id, row[0])
    ).fetchone()[0]
    if count < SUMMARY_AFTER:
        return
    storage._conn.execute("UPDATE chat_digest_state SET summarized = 1 WHERE chat_id = ?", (chat_id,))
    storage._conn.commit()
    try:
        summary = await summarize_chat(chat_id, title)
    except Exception:
        logger.exception("Не удалось собрать сводку по новой группе %s", chat_id)
        storage._conn.execute("UPDATE chat_digest_state SET summarized = 0 WHERE chat_id = ?", (chat_id,))
        storage._conn.commit()
        return
    await _send(context, config.OWNER_USER_ID, f"Коротко о новой группе «{title}»:\n\n{summary}")
