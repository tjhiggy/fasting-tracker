import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("fasting.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_utc TEXT NOT NULL,
                end_utc   TEXT,
                notes     TEXT
            )
        """)
        conn.commit()