import aiosqlite
from config import DATABASE_URL

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS cards (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    card_key      TEXT UNIQUE NOT NULL,
    duration_days INTEGER NOT NULL DEFAULT 30,
    status        TEXT NOT NULL DEFAULT 'unused',
    created_at    INTEGER NOT NULL,
    batch_id      TEXT
);

CREATE TABLE IF NOT EXISTS activations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    card_key     TEXT NOT NULL,
    device_id    TEXT NOT NULL,
    activated_at INTEGER NOT NULL,
    expire_at    INTEGER NOT NULL,
    is_active    INTEGER NOT NULL DEFAULT 1,
    UNIQUE(card_key)
);

CREATE TABLE IF NOT EXISTS deliveries (
    order_id     TEXT PRIMARY KEY,
    product_id   TEXT NOT NULL,
    quantity     INTEGER NOT NULL,
    cards_json   TEXT NOT NULL,
    created_at   INTEGER NOT NULL
);
"""

async def get_db():
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        yield db

async def init_db():
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.executescript(CREATE_TABLES_SQL)
        await db.commit()
        print(f"[DB] Initialized: {DATABASE_URL}")
