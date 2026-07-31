import secrets
import string
import time
import aiosqlite
from config import DATABASE_URL


def _rand_segment(n: int = 4) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(n))


def generate_card_key() -> str:
    """生成卡密，格式：SX-XXXX-XXXX-XXXX"""
    return f"SX-{_rand_segment()}-{_rand_segment()}-{_rand_segment()}"


async def create_cards_batch_in_db(
    db: aiosqlite.Connection,
    duration_days: int,
    count: int,
    batch_id: str = None,
) -> list:
    """Generate cards on an existing transaction without committing it."""
    now = int(time.time() * 1000)
    cards = []
    for _ in range(count):
        for attempt in range(10):
            key = generate_card_key()
            try:
                await db.execute(
                    "INSERT INTO cards (card_key, duration_days, created_at, batch_id) VALUES (?,?,?,?)",
                    (key, duration_days, now, batch_id)
                )
                cards.append(key)
                break
            except aiosqlite.IntegrityError:
                if attempt == 9:
                    raise RuntimeError("卡密生成重试次数过多")
    return cards


async def create_cards_batch(duration_days: int, count: int, batch_id: str = None) -> list:
    """批量生成卡密并写入数据库，返回卡密列表"""
    async with aiosqlite.connect(DATABASE_URL) as db:
        cards = await create_cards_batch_in_db(
            db, duration_days, count, batch_id
        )
        await db.commit()
    return cards
