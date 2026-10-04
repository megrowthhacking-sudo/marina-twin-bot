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
