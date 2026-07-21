import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from database import get_db
from core.card_gen import create_cards_batch
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
    if authorization.removeprefix("Bearer ").strip() != CARDNET_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Webhook 密钥错误")

    duration_days = PRODUCT_DURATION_MAP.get(req.product_id)
    if duration_days is None:
        raise HTTPException(status_code=400, detail=f"未知商品 ID: {req.product_id}")
    if req.quantity < 1 or req.quantity > 100:
        raise HTTPException(status_code=400, detail="quantity 范围 1-100")

    cards = await create_cards_batch(
        duration_days=duration_days,
        count=req.quantity,
        batch_id=req.order_id
    )
    return {"code": 200, "cards": cards}


# ── 管理员批量生成卡密 ────────────────────────────────

class GenRequest(BaseModel):
    duration_days: int
    count:         int
    admin_api_key: str


@router.post("/generate")
async def generate(req: GenRequest):
    if req.admin_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="无权限")
    if req.count < 1 or req.count > 1000:
        raise HTTPException(status_code=400, detail="count 范围 1-1000")
    cards = await create_cards_batch(req.duration_days, req.count)
    return {"code": 200, "count": len(cards), "cards": cards}


# ── 管理员查询卡密 ────────────────────────────────────

@router.get("/status/{card_key}")
async def card_status(
    card_key: str,
    admin_api_key: str,
    db: aiosqlite.Connection = Depends(get_db)
):
    if admin_api_key != ADMIN_API_KEY:
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
