"""/chatexport: выгрузка накопленной переписки группы текстовым файлом (09.10.2026, по просьбе владелицы).
Бот сохраняет в group_messages все текстовые сообщения групп, которые видел с момента
добавления (Telegram не отдаёт ботам историю до добавления). Команда показывает кнопками
список групп и присылает в личку .txt со всей накопленной перепиской. Только владелица и
только в личке. Модуль отдельный, потому что bot.py запускается как __main__;
chat_digest.register(app) сам вызывает chat_export.register(app)."""
import io
import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes
import config
import storage

logger = logging.getLogger("marina_twin_bot")


def _is_owner(user) -> bool:
    return user is not None and config.OWNER_USER_ID is not None and user.id == config.OWNER_USER_ID


def _fmt(ts: float, tz: ZoneInfo) -> str:
    return datetime.fromtimestamp(ts, tz).strftime("%d.%m.%Y %H:%M")


def build_export(chat_id: int, title: str) -> tuple[str, bytes, int]:
    """(имя файла, содержимое .txt в UTF-8, число сообщений). Если сообщений нет, число 0."""
    rows = storage._conn.execute(
        "SELECT user_name, telegram_username, text, ts FROM group_messages WHERE chat_id = ? ORDER BY id ASC",
        (chat_id,),
    ).fetchall()
    tz = ZoneInfo(config.MARINATWIN_TIMEZONE)
    slug = re.sub(r"[^\w\-]+", "_", title, flags=re.UNICODE).strip("_")[:40] or str(abs(chat_id))
    if not rows:
        return f"{slug}.txt", b"", 0
    joined = None
    try:
        row = storage._conn.execute("SELECT joined_at FROM chat_digest_state WHERE chat_id = ?", (chat_id,)).fetchone()
        joined = row[0] if row else None
    except Exception:
        joined = None
    start_ts = joined if joined else rows[0][3]
    lines = [
        f"Чат: {title}",
        f"Переписка с {_fmt(start_ts, tz)} по {_fmt(rows[-1][3], tz)} ({config.MARINATWIN_TIMEZONE})",
        f"Сообщений: {len(rows)}",
        "Только текст (и подписи), который бот видел после добавления в группу. Фото, голосовые и файлы без подписи не сохраняются.",
        "",
    ]
    for name, username, text, ts in rows:
        who = name or "?"
        if username:
            who += f" (@{username})"
        body = (text or "").replace("\r", "").split("\n")
        lines.append(f"[{_fmt(ts, tz)}] {who}: {body[0]}")
        lines.extend(" " + part for part in body[1:])
    stamp = datetime.now(tz).strftime("%Y%m%d")
    return f"{slug}_{stamp}.txt", "\n".join(lines).encode("utf-8"), len(rows)


async def handle_chatexport_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None or chat.type != "private" or not _is_owner(update.effective_user):
        return
    groups = storage.get_known_group_chats(limit=30)
    if not groups:
        await update.message.reply_text("Я пока не видела ни одной группы.")
        return
    counts = dict(storage._conn.execute("SELECT chat_id, COUNT(*) FROM group_messages GROUP BY chat_id").fetchall())
    rows = [
        [InlineKeyboardButton(f"{title[:40]} ({counts.get(cid, 0)})", callback_data=f"chx:{cid}")]
        for cid, title in groups
    ]
    await update.message.reply_text(
        "Из какого чата выгрузить переписку файлом? В скобках число сохранённых сообщений.",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def handle_chatexport_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat = update.effective_chat
    if chat is None or chat.type != "private" or not _is_owner(query.from_user):
        return
    try:
        chat_id = int((query.data or "").split(":", 1)[1])
    except (IndexError, ValueError):
        return
    title = dict(storage.get_known_group_chats(limit=100)).get(chat_id, str(chat_id))
    try:
        filename, data, count = build_export(chat_id, title)
    except Exception:
        logger.exception("chat_export: не удалось собрать файл чата %s", chat_id)
        await context.bot.send_message(chat_id=chat.id, text="Не получилось собрать файл, попробуй ещё раз чуть позже.")
        return
    if count == 0:
        await context.bot.send_message(chat_id=chat.id, text="В этом чате у меня пока нет сохранённых сообщений.")
        return
    await context.bot.send_document(
        chat_id=chat.id,
        document=io.BytesIO(data),
        filename=filename,
        caption=f"Переписка «{title}», сообщений: {count}",
    )


def register(app) -> None:
    """Регистрирует /chatexport и кнопки выбора чата."""
    app.add_handler(CommandHandler("chatexport", handle_chatexport_command))
    app.add_handler(CallbackQueryHandler(handle_chatexport_callback, pattern=r"^chx:"))
