import aiosqlite
import hmac
import json
import time
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from database import get_db
from core.card_gen import create_cards_batch, create_cards_batch_in_db
from config import CARDNET_WEBHOOK_SECRET, ADMIN_API_KEY

router = APIRouter(prefix="/api/cards", tags=["cards"])

# 商品 ID → 有效天数映射（-1 = 永久）
PRODUCT_DURATION_MAP = {
    "sx_7d":   7,
    "sx_30d":  30,
    "sx_90d":  90,
    "sx_365d": 365,
    "sx_perm": -1,
}


# ── 三方卡网发货 Webhook ──────────────────────────────

class DeliverRequest(BaseModel):
    order_id:   str
    product_id: str
    quantity:   int = 1


@router.post("/deliver")
async def deliver(
    req: DeliverRequest,
    authorization: str = Header(...),
    db: aiosqlite.Connection = Depends(get_db)
):
    supplied_secret = authorization.removeprefix("Bearer ").strip()
    if not hmac.compare_digest(supplied_secret, CARDNET_WEBHOOK_SECRET):
        raise HTTPException(status_code=403, detail="Webhook 密钥错误")

    duration_days = PRODUCT_DURATION_MAP.get(req.product_id)
    if duration_days is None:
        raise HTTPException(status_code=400, detail=f"未知商品 ID: {req.product_id}")
    if req.quantity < 1 or req.quantity > 100:
        raise HTTPException(status_code=400, detail="quantity 范围 1-100")

    order_id = req.order_id.strip()
    if not order_id or len(order_id) > 128:
        raise HTTPException(status_code=400, detail="order_id 长度范围 1-128")

    # Serialize delivery creation so concurrent retries observe the same result.
    await db.execute("BEGIN IMMEDIATE")
    try:
        async with db.execute(
            "SELECT product_id, quantity, cards_json FROM deliveries WHERE order_id=?",
            (order_id,),
        ) as cur:
            existing = await cur.fetchone()
        if existing:
            if (existing["product_id"] != req.product_id
                    or existing["quantity"] != req.quantity):
                raise HTTPException(status_code=409, detail="order_id 参数与首次请求不一致")
            cards = json.loads(existing["cards_json"])
            await db.commit()
            return {"code": 200, "cards": cards, "idempotent_replay": True}

        # Backfill idempotency for orders delivered before the deliveries table
        # was introduced.
        async with db.execute(
            "SELECT card_key, duration_days FROM cards WHERE batch_id=? ORDER BY id",
            (order_id,),
        ) as cur:
            legacy_rows = await cur.fetchall()
        if legacy_rows:
            if (len(legacy_rows) != req.quantity
                    or any(row["duration_days"] != duration_days for row in legacy_rows)):
                raise HTTPException(status_code=409, detail="order_id 已存在但参数不一致")
            cards = [row["card_key"] for row in legacy_rows]
        else:
            cards = await create_cards_batch_in_db(
                db, duration_days, req.quantity, order_id
            )

        await db.execute(
            "INSERT INTO deliveries (order_id, product_id, quantity, cards_json, created_at) "
            "VALUES (?,?,?,?,?)",
            (order_id, req.product_id, req.quantity,
             json.dumps(cards, separators=(",", ":")), int(time.time() * 1000)),
        )
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise
    return {"code": 200, "cards": cards}


# ── 管理员批量生成卡密 ────────────────────────────────

class GenRequest(BaseModel):
    duration_days: int
    count:         int
    admin_api_key: str


@router.post("/generate")
async def generate(req: GenRequest):
    if not hmac.compare_digest(req.admin_api_key, ADMIN_API_KEY):
        raise HTTPException(status_code=403, detail="无权限")
    if req.count < 1 or req.count > 1000:
        raise HTTPException(status_code=400, detail="count 范围 1-1000")
    cards = await create_cards_batch(req.duration_days, req.count)
    return {"code": 200, "count": len(cards), "cards": cards}


# ── 管理员查询卡密 ────────────────────────────────────

@router.get("/status/{card_key}")
async def card_status(
    card_key: str,
    admin_api_key: str | None = None,
    x_admin_api_key: str | None = Header(default=None, alias="X-Admin-Api-Key"),
    db: aiosqlite.Connection = Depends(get_db)
):
    supplied_key = x_admin_api_key or admin_api_key or ""
    if not hmac.compare_digest(supplied_key, ADMIN_API_KEY):
        raise HTTPException(status_code=403, detail="无权限")

    async with db.execute("SELECT * FROM cards WHERE card_key=?", (card_key,)) as cur:
        card = await cur.fetchone()
    if not card:
        raise HTTPException(status_code=404, detail="卡密不存在")

    async with db.execute(
        "SELECT device_id, activated_at, expire_at, is_active FROM activations WHERE card_key=?",
        (card_key,)
    ) as cur:
        act = await cur.fetchone()

    return {
        "card_key":      card_key,
        "status":        card["status"],
        "duration_days": card["duration_days"],
        "activation":    dict(act) if act else None
    }
