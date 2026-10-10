"""
API Key Authentication Service
- Development mode: auth bypass
- Production mode: key required
- Keys stored in SQLite (zero setup)
"""

import sqlite3
import secrets
import hashlib
import os
from datetime import datetime
from loguru import logger


DB_PATH = "data/keys.db"
os.makedirs("data", exist_ok=True)


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_hash TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_used_at TEXT,
            request_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Auth DB initialized")


def generate_key(name: str, email: str = "") -> str:
    raw_key = f"im_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    conn = _get_conn()
    conn.execute(
        "INSERT INTO api_keys (key_hash, name, email) VALUES (?, ?, ?)",
        (key_hash, name, email)
    )
    conn.commit()
    conn.close()
    logger.info(f"API key generated for: {name}")
    return raw_key


def validate_key(raw_key: str) -> bool:
    if not raw_key:
        return False
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    conn = _get_conn()
    row = conn.execute(
        "SELECT id, is_active FROM api_keys WHERE key_hash = ?",
        (key_hash,)
    ).fetchone()

    if row and row["is_active"]:
        conn.execute(
            "UPDATE api_keys SET last_used_at = ?, request_count = request_count + 1 WHERE key_hash = ?",
            (datetime.utcnow().isoformat(), key_hash)
        )
        conn.commit()
        conn.close()
        return True

    conn.close()
    return False


def list_keys() -> list:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, name, email, is_active, created_at, last_used_at, request_count FROM api_keys"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def revoke_key(key_id: int) -> bool:
    conn = _get_conn()
    conn.execute("UPDATE api_keys SET is_active = 0 WHERE id = ?", (key_id,))
    conn.commit()
    conn.close()
    return True
