"""SQLite-backed chat session persistence for Archivist chat."""

import os
import sqlite3
import time
import uuid
from pathlib import Path

_DATA_DIR = Path("/data") if Path("/data").exists() and os.access("/data", os.W_OK) else Path(".")
DB_PATH = _DATA_DIR / "chat.db"

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created_at);
"""


def _get_db() -> sqlite3.Connection:
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db


def init_db():
    with _get_db() as db:
        db.executescript(_CREATE_SQL)


def create_session(title: str = "") -> dict:
    sid = uuid.uuid4().hex[:12]
    now = time.time()
    with _get_db() as db:
        db.execute(
            "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (sid, title, now, now),
        )
    return {"id": sid, "title": title, "created_at": now, "updated_at": now}


def list_sessions() -> list[dict]:
    with _get_db() as db:
        rows = db.execute(
            """
            SELECT s.id, s.title, s.created_at, s.updated_at,
                   COUNT(m.id) AS message_count,
                   (SELECT content FROM messages WHERE session_id = s.id ORDER BY created_at DESC LIMIT 1) AS last_message
            FROM sessions s
            LEFT JOIN messages m ON m.session_id = s.id
            GROUP BY s.id
            ORDER BY s.updated_at DESC
            """
        ).fetchall()
        return [
            {
                "id": r["id"],
                "title": r["title"],
                "updated_at": r["updated_at"],
                "message_count": r["message_count"],
                "last_message": (r["last_message"] or "")[:80],
            }
            for r in rows
        ]


def get_session_messages(session_id: str) -> list[dict]:
    with _get_db() as db:
        rows = db.execute(
            "SELECT id, role, content, created_at FROM messages WHERE session_id = ? ORDER BY created_at",
            (session_id,),
        ).fetchall()
        return [{"id": r["id"], "role": r["role"], "content": r["content"], "created_at": r["created_at"]} for r in rows]


def add_message(session_id: str, role: str, content: str) -> dict:
    now = time.time()
    with _get_db() as db:
        cursor = db.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, now),
        )
        msg_id = cursor.lastrowid
        db.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
    return {"id": msg_id, "role": role, "content": content, "created_at": now}


def update_session_title(session_id: str, title: str):
    with _get_db() as db:
        db.execute("UPDATE sessions SET title = ? WHERE id = ?", (title, session_id))


def delete_session(session_id: str):
    with _get_db() as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
