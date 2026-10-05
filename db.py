import sqlite3
from datetime import datetime

DB_PATH = "langtime.db"

def get_connection():
    """Åbner forbindelse til databasen. Skabes automatisk første gang."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # giver ordbogs-lignende adgang til rækker
    return conn

def init_db():
    """Opretter tabellerne. Kan køres så tit som muligt — CREATE TABLE IF NOT EXISTS."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL UNIQUE,
                translation TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                lookups INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

def get_word(word: str):
    """Henter ét ord, eller None hvis det ikke findes."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM words WHERE word = ?", (word,)
        ).fetchone()
        return dict(row) if row else None

def upsert_word(word: str, translation: str, status: str):
    """Indsætter et nyt ord eller opdaterer et eksisterende."""
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO words (word, translation, status, lookups, created_at, updated_at)
            VALUES (?, ?, ?, 1, ?, ?)
            ON CONFLICT(word) DO UPDATE SET
                translation = excluded.translation,
                status = excluded.status,
                lookups = lookups + 1,
                updated_at = excluded.updated_at
        """, (word, translation, status, now, now))

def get_words_bulk(words: list[str]):
    """Henter alle kendte ord fra en liste — til at farve teksten ved rendering."""
    if not words:
        return {}
    placeholders = ",".join("?" * len(words))
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT word, status FROM words WHERE word IN ({placeholders})", words
        ).fetchall()
        return {row["word"]: row["status"] for row in rows}