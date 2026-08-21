"""
Хранилище истории переписки и "прилипших" стран по каждому чату.
SQLite-файл на диске — чтобы при перезапуске бота (деплой, рестарт контейнера)
разговоры не терялись.
"""

import json
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "marina_twin.db"

# Сколько последних сообщений (с обеих сторон) держим в истории одного чата.
# При 1M-контексте это не про лимит токенов, а про разумную стоимость/скорость запроса.
MAX_HISTORY_MESSAGES = 40


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER PRIMARY KEY,
            history_json TEXT NOT NULL DEFAULT '[]',
            active_countries_json TEXT NOT NULL DEFAULT '[]',
            greeted INTEGER NOT NULL DEFAULT 0,
            updated_at REAL NOT NULL
        )
        """
    )
    # Буфер сообщений групповых чатов — Marina Twin тут молча слушает и
    # копит переписку, пока не придёт время выгрузить задачи в ClickUp.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS group_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            chat_title TEXT,
            user_name TEXT,
            text TEXT NOT NULL,
            ts REAL NOT NULL,
            flushed INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_group_messages_chat_flushed ON group_messages(chat_id, flushed)")
    # Журнал того, что реально улетело в ClickUp — для отладки и чтобы не гадать задним числом.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pushed_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            chat_title TEXT,
            clickup_task_id TEXT,
            title TEXT,
            created_at REAL NOT NULL
        )
        """
    )
    conn.commit()
    return conn


_conn = _connect()


def get_chat(chat_id: int) -> dict:
    row = _conn.execute(
        "SELECT history_json, active_countries_json, greeted FROM chats WHERE chat_id = ?",
        (chat_id,),
    ).fetchone()
    if row is None:
        return {"history": [], "active_countries": [], "greeted": False}
    history_json, countries_json, greeted = row
    return {
        "history": json.loads(history_json),
        "active_countries": json.loads(countries_json),
        "greeted": bool(greeted),
    }


def save_chat(chat_id: int, history: list, active_countries: list, greeted: bool) -> None:
    if len(history) > MAX_HISTORY_MESSAGES:
        history = history[-MAX_HISTORY_MESSAGES:]
    _conn.execute(
        """
        INSERT INTO chats (chat_id, history_json, active_countries_json, greeted, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET
            history_json = excluded.history_json,
            active_countries_json = excluded.active_countries_json,
            greeted = excluded.greeted,
            updated_at = excluded.updated_at
        """,
        (chat_id, json.dumps(history, ensure_ascii=False),
         json.dumps(active_countries, ensure_ascii=False), int(greeted), time.time()),
    )
    _conn.commit()


def reset_chat(chat_id: int) -> None:
    _conn.execute("DELETE FROM chats WHERE chat_id = ?", (chat_id,))
    _conn.commit()


# --- Буфер групповых сообщений (сбор задач для ClickUp) ---

def add_group_message(chat_id: int, chat_title: str, user_name: str, text: str) -> None:
    _conn.execute(
        "INSERT INTO group_messages (chat_id, chat_title, user_name, text, ts, flushed) VALUES (?, ?, ?, ?, ?, 0)",
        (chat_id, chat_title, user_name, text, time.time()),
    )
    _conn.commit()


def get_unflushed(chat_id: int) -> list[dict]:
    rows = _conn.execute(
        "SELECT user_name, text, ts FROM group_messages WHERE chat_id = ? AND flushed = 0 ORDER BY ts ASC",
        (chat_id,),
    ).fetchall()
    return [{"user_name": r[0], "text": r[1], "ts": r[2]} for r in rows]


def mark_flushed(chat_id: int) -> None:
    _conn.execute("UPDATE group_messages SET flushed = 1 WHERE chat_id = ? AND flushed = 0", (chat_id,))
    _conn.commit()


def get_chats_with_pending() -> list[tuple[int, str]]:
    """Список (chat_id, chat_title) групп, у которых есть невыгруженные сообщения."""
    rows = _conn.execute(
        """
        SELECT chat_id, MAX(chat_title)
        FROM group_messages
        WHERE flushed = 0
        GROUP BY chat_id
        """
    ).fetchall()
    return [(r[0], r[1] or str(r[0])) for r in rows]


def log_pushed_task(chat_id: int, chat_title: str, clickup_task_id: str, title: str) -> None:
    _conn.execute(
        "INSERT INTO pushed_tasks (chat_id, chat_title, clickup_task_id, title, created_at) VALUES (?, ?, ?, ?, ?)",
        (chat_id, chat_title, clickup_task_id, title, time.time()),
    )
    _conn.commit()
