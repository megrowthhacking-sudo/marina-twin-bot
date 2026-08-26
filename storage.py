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
    # Журнал того, что реально улетело в ClickUp — для отладки, отчётов по /tasksX
    # (см. get_pushed_tasks_by_project) и чтобы не гадать задним числом.
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
    # project ("atlas"/"altyn"/"bestswift"/"unsorted") — в какой список ClickUp реально
    # ушла задача; нужно для отчёта по /tasksX (список всех задач проекта). Старые строки
    # (до этой миграции) останутся с project = NULL и не попадут в отчёты — это ок,
    # это лишь исторический пробел.
    _ensure_columns(conn, "pushed_tasks", {"project": "TEXT"})
    # За каким проектом (ключ из config.CLICKUP_PROJECTS: "atlas"/"altyn"/"bestswift")
    # закреплён групповой чат. Проставляется автоматически либо когда кто-то в чате пишет
    # "эта группа про задачи <проект>", либо при вызове команды /tasksatlas /tasksaltyn
    # /tasksbs — дальше периодическая автовыгрузка уже знает, в какой список ClickUp
    # слать задачи из этого чата.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_projects (
            chat_id INTEGER PRIMARY KEY,
            project TEXT NOT NULL,
            updated_at REAL NOT NULL
        )
        """
    )
    # Вопросы из групп, адресованные "Марине" (упоминание/имя/reply на её сообщение),
    # ожидающие ответа владелицы в личке. См. эскалацию в bot.py.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pending_escalations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_chat_id INTEGER NOT NULL,
            group_title TEXT,
            asker_name TEXT,
            question TEXT NOT NULL,
            created_at REAL NOT NULL,
            resolved INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    # Поддержка правок/дополнений к уже отправленному ответу (см. bot.py,
    # _propose_escalation_correction): Марина тегает (reply) в личке исходное
    # пересланное сообщение с вопросом — dm_question_message_id как раз и нужен, чтобы
    # понять, к какой эскалации относится её reply, даже если та уже resolved.
    # last_answer/last_posted_text — то, что реально ушло в группу в прошлый раз (нужно
    # показывать как контекст в следующей правке). draft_raw/draft_posted — черновик
    # правки, ждущий подтверждения (кнопки "Отправить"/"Не отправлять") — можно
    # присылать новые правки поверх ещё не подтверждённой, последняя всегда побеждает.
    _ensure_columns(
        conn,
        "pending_escalations",
        {
            "dm_question_message_id": "INTEGER",
            "last_answer": "TEXT",
            "last_posted_text": "TEXT",
            "draft_raw": "TEXT",
            "draft_posted": "TEXT",
            "flow_stage": "TEXT",
        },
    )
    # Задачи из "смешанных" (непривязанных к проекту) чатов, для которых Claude не смог
    # по контексту понять, к какому проекту они относятся ("unsorted" в classify-ответе).
    # Вместо того чтобы молча класть их в "Разобрать", бот спрашивает прямо в чате —
    # question_message_id это message_id того вопроса, чтобы позже сматчить reply на
    # него (см. handle_group_message в bot.py). Если никто не ответит —
    # periodic_flush_job по таймауту (CLICKUP_CLASSIFICATION_TIMEOUT_MINUTES) сам
    # положит задачу в "Разобрать".
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pending_classifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            chat_title TEXT,
            task_title TEXT NOT NULL,
            task_description TEXT,
            task_priority TEXT,
            question_message_id INTEGER,
            created_at REAL NOT NULL,
            resolved INTEGER NOT NULL DEFAULT 0,
            resolved_project TEXT
        )
        """
    )
    # Имя исполнителя, извлечённое из текста задачи (см. _resolve_assignee_id в bot.py) —
    # нужно сохранить и для неоднозначных (по проекту) задач, чтобы после ответа на
    # уточняющий вопрос (или по таймауту) назначить исполнителя так же, как это уже
    # делается для задач с сразу понятным проектом.
    _ensure_columns(conn, "pending_classifications", {"task_assignee_name": "TEXT"})
    # Все DM-сообщения бота, связанные с одной эскалацией (исходный пересланный вопрос,
    # подтверждение ответа, черновики правок) — чтобы Марина могла сделать reply-правку
    # на ЛЮБОЕ из них, а не только на самое первое сообщение (см.
    # get_escalation_by_any_dm_message_id ниже и link_escalation_dm_message в bot.py).
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS escalation_dm_messages (
            message_id INTEGER PRIMARY KEY,
            escalation_id INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def _ensure_columns(conn: sqlite3.Connection, table: str, columns: dict) -> None:
    """Простая миграция "на лету": добавляет недостающие колонки в уже существующую
    (на проде) таблицу, не трогая существующие данные."""
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    for name, coltype in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {coltype}")


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


def log_pushed_task(chat_id: int, chat_title: str, clickup_task_id: str, title: str, project: str | None = None) -> None:
    _conn.execute(
        "INSERT INTO pushed_tasks (chat_id, chat_title, clickup_task_id, title, project, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (chat_id, chat_title, clickup_task_id, title, project, time.time()),
    )
    _conn.commit()


def get_pushed_tasks_by_project(project: str) -> list[dict]:
    """Все когда-либо созданные ботом задачи по одному проекту (из всех чатов),
    в порядке создания — для отчёта по команде /tasksX (см. _send_project_report в
    bot.py)."""
    rows = _conn.execute(
        "SELECT title, chat_title, created_at FROM pushed_tasks WHERE project = ? ORDER BY created_at ASC",
        (project,),
    ).fetchall()
    return [{"title": r[0], "chat_title": r[1], "created_at": r[2]} for r in rows]


# --- Привязка чата к проекту ClickUp (atlas / altyn / bestswift) ---

def get_chat_project(chat_id: int) -> str | None:
    row = _conn.execute("SELECT project FROM chat_projects WHERE chat_id = ?", (chat_id,)).fetchone()
    return row[0] if row else None


def set_chat_project(chat_id: int, project: str) -> None:
    _conn.execute(
        """
        INSERT INTO chat_projects (chat_id, project, updated_at) VALUES (?, ?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET project = excluded.project, updated_at = excluded.updated_at
        """,
        (chat_id, project, time.time()),
    )
    _conn.commit()


# --- Отложенные вопросы из групп ("эскалация" к владелице в личку) ---

def add_pending_escalation(group_chat_id: int, group_title: str, asker_name: str, question: str) -> int:
    cur = _conn.execute(
        """
        INSERT INTO pending_escalations (group_chat_id, group_title, asker_name, question, created_at, resolved)
        VALUES (?, ?, ?, ?, ?, 0)
        """,
        (group_chat_id, group_title, asker_name, question, time.time()),
    )
    _conn.commit()
    return cur.lastrowid


def get_oldest_pending_escalation() -> tuple[int, int, str, str, str] | None:
    """Возвращает (id, group_chat_id, group_title, asker_name, question) самого старого
    неотвеченного вопроса, или None, если очередь пуста."""
    row = _conn.execute(
        """
        SELECT id, group_chat_id, group_title, asker_name, question
        FROM pending_escalations
        WHERE resolved = 0
        ORDER BY created_at ASC
        LIMIT 1
        """
    ).fetchone()
    return tuple(row) if row else None


def resolve_pending_escalation(escalation_id: int) -> None:
    _conn.execute("UPDATE pending_escalations SET resolved = 1 WHERE id = ?", (escalation_id,))
    _conn.commit()


_ESCALATION_COLUMNS = (
    "id", "group_chat_id", "group_title", "asker_name", "question", "resolved",
    "dm_question_message_id", "last_answer", "last_posted_text", "draft_raw", "draft_posted",
    "flow_stage",
)


def get_escalation(escalation_id: int) -> dict | None:
    """Полная запись эскалации по id — включая историю последнего ответа и
    незавершённый черновик правки, если есть."""
    row = _conn.execute(
        f"SELECT {', '.join(_ESCALATION_COLUMNS)} FROM pending_escalations WHERE id = ?",
        (escalation_id,),
    ).fetchone()
    return dict(zip(_ESCALATION_COLUMNS, row)) if row else None


def get_escalation_by_dm_message_id(message_id: int) -> dict | None:
    """Находит эскалацию по message_id пересланного вопроса в личке владелицы — так
    понимаем, что reply на это сообщение относится именно к этому вопросу, даже если
    он уже resolved (правка/дополнение к уже отправленному ответу)."""
    row = _conn.execute(
        "SELECT id FROM pending_escalations WHERE dm_question_message_id = ?",
        (message_id,),
    ).fetchone()
    return get_escalation(row[0]) if row else None


def set_escalation_dm_message_id(escalation_id: int, message_id: int) -> None:
    _conn.execute(
        "UPDATE pending_escalations SET dm_question_message_id = ? WHERE id = ?",
        (message_id, escalation_id),
    )
    _conn.commit()


def link_escalation_dm_message(escalation_id: int, message_id: int) -> None:
    """Запоминает, что это DM-сообщение бота относится к эскалации — чтобы reply на
    него (не только на самое первое пересланное сообщение) тоже находил нужную
    эскалацию, см. get_escalation_by_any_dm_message_id. Вызывается на каждое
    отправленное владелице сообщение по ходу эскалации (исходный вопрос, подтверждение
    ответа, черновик правки)."""
    _conn.execute(
        "INSERT OR REPLACE INTO escalation_dm_messages (message_id, escalation_id) VALUES (?, ?)",
        (message_id, escalation_id),
    )
    _conn.commit()


def get_escalation_by_any_dm_message_id(message_id: int) -> dict | None:
    """Как get_escalation_by_dm_message_id, но проверяет ВСЕ DM-сообщения, связанные с
    эскалацией (см. link_escalation_dm_message), а не только самое первое — на случай
    если Марина отвечает reply-ом на более позднее сообщение (подтверждение ответа,
    черновик правки), а не на исходный пересланный вопрос."""
    row = _conn.execute(
        "SELECT escalation_id FROM escalation_dm_messages WHERE message_id = ?",
        (message_id,),
    ).fetchone()
    if row:
        return get_escalation(row[0])
    return get_escalation_by_dm_message_id(message_id)


def update_escalation_after_answer(escalation_id: int, raw_answer: str, posted_text: str) -> None:
    """Фиксирует ответ (первый или очередная правка) как resolved + запоминает, что
    реально ушло в группу — это станет "предыдущим ответом" для следующей правки."""
    _conn.execute(
        "UPDATE pending_escalations SET resolved = 1, flow_stage = NULL, last_answer = ?, last_posted_text = ? WHERE id = ?",
        (raw_answer, posted_text, escalation_id),
    )
    _conn.commit()


def set_escalation_flow_stage(escalation_id: int, stage: str | None) -> None:
    _conn.execute(
        "UPDATE pending_escalations SET flow_stage = ? WHERE id = ?",
        (stage, escalation_id),
    )
    _conn.commit()


def cancel_escalation_flow(escalation_id: int) -> None:
    _conn.execute(
        """
        UPDATE pending_escalations
        SET resolved = 1, flow_stage = NULL, draft_raw = NULL, draft_posted = NULL
        WHERE id = ?
        """,
        (escalation_id,),
    )
    _conn.commit()


def set_escalation_draft(escalation_id: int, raw_text: str, posted_text: str) -> None:
    _conn.execute(
        "UPDATE pending_escalations SET draft_raw = ?, draft_posted = ? WHERE id = ?",
        (raw_text, posted_text, escalation_id),
    )
    _conn.commit()


def clear_escalation_draft(escalation_id: int) -> None:
    _conn.execute(
        "UPDATE pending_escalations SET draft_raw = NULL, draft_posted = NULL WHERE id = ?",
        (escalation_id,),
    )
    _conn.commit()


# --- Уточнение проекта для неоднозначных задач в "смешанных" чатах ---

_CLASSIFICATION_COLUMNS = (
    "id", "chat_id", "chat_title", "task_title", "task_description", "task_priority",
    "question_message_id", "created_at", "resolved", "resolved_project", "task_assignee_name",
)


def add_pending_classification(
    chat_id: int, chat_title: str, task_title: str, task_description: str, task_priority: str | None,
    task_assignee_name: str | None = None,
) -> int:
    cur = _conn.execute(
        """
        INSERT INTO pending_classifications
        (chat_id, chat_title, task_title, task_description, task_priority, task_assignee_name, created_at, resolved)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """,
        (chat_id, chat_title, task_title, task_description, task_priority, task_assignee_name, time.time()),
    )
    _conn.commit()
    return cur.lastrowid


def set_classification_question_message_id(classification_id: int, message_id: int) -> None:
    _conn.execute(
        "UPDATE pending_classifications SET question_message_id = ? WHERE id = ?",
        (message_id, classification_id),
    )
    _conn.commit()


def get_classification_by_question_message_id(chat_id: int, message_id: int) -> dict | None:
    """Находит неотвеченную классификацию по (chat_id, message_id) уточняющего вопроса.
    ВАЖНО: message_id уникален только в пределах одного чата в Telegram — в отличие от
    эскалаций (те все в одной личке с владелицей), уточняющие вопросы разлетаются по
    разным группам, так что chat_id обязателен, иначе можно случайно смэтчить чужой чат."""
    row = _conn.execute(
        f"""
        SELECT {', '.join(_CLASSIFICATION_COLUMNS)} FROM pending_classifications
        WHERE chat_id = ? AND question_message_id = ? AND resolved = 0
        """,
        (chat_id, message_id),
    ).fetchone()
    return dict(zip(_CLASSIFICATION_COLUMNS, row)) if row else None


def resolve_classification(classification_id: int, project: str) -> None:
    _conn.execute(
        "UPDATE pending_classifications SET resolved = 1, resolved_project = ? WHERE id = ?",
        (project, classification_id),
    )
    _conn.commit()


def get_unresolved_classifications_older_than(cutoff_ts: float) -> list[dict]:
    """Для таймаута (см. periodic_flush_job): классификации, на которые никто не
    ответил дольше CLICKUP_CLASSIFICATION_TIMEOUT_MINUTES — их пора принудительно
    положить в "Разобрать"."""
    rows = _conn.execute(
        f"""
        SELECT {', '.join(_CLASSIFICATION_COLUMNS)} FROM pending_classifications
        WHERE resolved = 0 AND created_at < ?
        """,
        (cutoff_ts,),
    ).fetchall()
    return [dict(zip(_CLASSIFICATION_COLUMNS, r)) for r in rows]


def get_chats_with_pending_and_project() -> list[tuple[int, str, str]]:
    """Список (chat_id, chat_title, project) — только чаты, у которых есть и невыгруженные
    сообщения, и уже известный проект (назначается командой /tasks<project>). Чаты без
    привязанного проекта периодическая автовыгрузка пропускает — ей некуда слать задачи."""
    rows = _conn.execute(
        """
        SELECT gm.chat_id, MAX(gm.chat_title), cp.project
        FROM group_messages gm
        JOIN chat_projects cp ON cp.chat_id = gm.chat_id
        WHERE gm.flushed = 0
        GROUP BY gm.chat_id
        """
    ).fetchall()
    return [(r[0], r[1] or str(r[0]), r[2]) for r in rows]
