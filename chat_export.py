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
