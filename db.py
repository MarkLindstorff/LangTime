import sqlite3
from datetime import datetime

DB_PATH = "langtime.db"

def get_connection():
    """Åbner forbindelse til databasen. Skabes automatisk første gang."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                translation TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                lang TEXT NOT NULL DEFAULT 'da',
                lookups INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(word, lang)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS texts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source_lang TEXT NOT NULL DEFAULT 'ru',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

def get_setting(key: str, default: str = "") -> str:
    """Henter en indstilling, eller default hvis den ikke findes."""
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

def set_setting(key: str, value: str):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, value))

def get_word(word: str, lang: str):
    """Henter ét ord for et givent målsprog, eller None."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM words WHERE word = ? AND lang = ?", (word, lang)
        ).fetchone()
        return dict(row) if row else None

def upsert_word(word: str, translation: str, status: str, lang: str = "da"):
    """Indsætter et nyt ord eller opdaterer et eksisterende (pr. målsprog)."""
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO words (word, translation, status, lang, lookups, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(word, lang) DO UPDATE SET
                translation = excluded.translation,
                status = excluded.status,
                lookups = lookups + 1,
                updated_at = excluded.updated_at
        """, (word, translation, status, lang, now, now))

def get_words_bulk(words: list[str], lang: str = "da"):
    """Henter alle kendte ord fra en liste for ét målsprog."""
    if not words:
        return {}
    placeholders = ",".join("?" * len(words))
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT word, status FROM words WHERE word IN ({placeholders}) AND lang = ?",
            words + [lang]
        ).fetchall()
        return {row["word"]: row["status"] for row in rows}

def add_text(title: str, content: str, source_lang: str = "ru") -> int:
    """Gemmer en tekst og returnerer dens nye id."""
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO texts (title, content, source_lang, created_at) VALUES (?, ?, ?, ?)",
            (title, content, source_lang, now)
        )
        return cursor.lastrowid

def list_texts():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id, title, source_lang, created_at FROM texts ORDER BY created_at DESC"
        )]

def get_text(text_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM texts WHERE id = ?", (text_id,)
        ).fetchone()
        return dict(row) if row else None