import time
import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from database import get_db
from core.auth import create_token, verify_token
from core.sign import verify_client_sign
from config import SERVER_SECRET, ADMIN_API_KEY

router = APIRouter(prefix="/api/license", tags=["license"])


# ── 数据模型 ──────────────────────────────────────────

class ActivateRequest(BaseModel):
    card_key:  str
    device_id: str
    sign:      str   # MD5(card_key + device_id + SERVER_SECRET).upper()


class LicenseResponse(BaseModel):
    code: int
    msg:  str
    data: dict | None = None


class UnbindRequest(BaseModel):
    card_key:      str
    admin_api_key: str


# ── 激活卡密 ──────────────────────────────────────────

@router.post("/activate", response_model=LicenseResponse)
async def activate(req: ActivateRequest, db: aiosqlite.Connection = Depends(get_db)):
    # 1. 验签
    verify_client_sign(req.card_key, req.device_id, req.sign, SERVER_SECRET)

    # 2. 查卡密
    async with db.execute("SELECT * FROM cards WHERE card_key=?", (req.card_key,)) as cur:
        card = await cur.fetchone()
    if not card:
        return LicenseResponse(code=400, msg="卡密不存在")
    if card["status"] == "revoked":
        return LicenseResponse(code=400, msg="卡密已作废")

    # 3. 查激活记录
    async with db.execute(
        "SELECT * FROM activations WHERE card_key=?", (req.card_key,)
    ) as cur:
        activation = await cur.fetchone()

    now_ms = int(time.time() * 1000)

    if activation:
        # 已有激活记录
        if not activation["is_active"]:
            return LicenseResponse(code=400, msg="卡密已被解绑，请联系客服重新激活")
        if activation["device_id"] != req.device_id:
            return LicenseResponse(code=400, msg="该卡密已绑定其他设备，如需换绑请联系客服")
        # 同设备重复激活 → 返回现有 token
        token = create_token(req.card_key, req.device_id, activation["expire_at"])
        return LicenseResponse(code=200, msg="激活成功", data={
            "token":     token,
            "expire_at": activation["expire_at"]
        })

    # 4. 首次激活
    duration_days = card["duration_days"]
    expire_at = -1 if duration_days == -1 else now_ms + duration_days * 86_400_000

    await db.execute(
        "INSERT INTO activations (card_key, device_id, activated_at, expire_at) VALUES (?,?,?,?)",
        (req.card_key, req.device_id, now_ms, expire_at)
    )
    await db.execute(
        "UPDATE cards SET status='activated' WHERE card_key=?", (req.card_key,)
    )
    await db.commit()

    token = create_token(req.card_key, req.device_id, expire_at)
    return LicenseResponse(code=200, msg="激活成功", data={
        "token":     token,
        "expire_at": expire_at
    })


# ── 鉴权校验 ──────────────────────────────────────────

@router.get("/verify", response_model=LicenseResponse)
async def verify(
    device_id: str,
    authorization: str = Header(...),
    db: aiosqlite.Connection = Depends(get_db)
):
    token = authorization.removeprefix("Bearer ").strip()
    payload = verify_token(token, device_id)
    if not payload:
        return LicenseResponse(code=401, msg="Token 无效或已过期", data={"valid": False})

    # 再查库确认未解绑
    async with db.execute(
        "SELECT is_active, expire_at FROM activations WHERE card_key=?",
        (payload["card_key"],)
    ) as cur:
        row = await cur.fetchone()

    if not row or not row["is_active"]:
        return LicenseResponse(code=401, msg="授权已失效", data={"valid": False})

    return LicenseResponse(code=200, msg="授权有效", data={
        "valid":     True,
        "expire_at": row["expire_at"]
    })


# ── 解绑设备（管理员）────────────────────────────────

@router.post("/unbind", response_model=LicenseResponse)
async def unbind(req: UnbindRequest, db: aiosqlite.Connection = Depends(get_db)):
    if req.admin_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="无权限")
    await db.execute(
        "UPDATE activations SET is_active=0 WHERE card_key=?", (req.card_key,)
    )
    await db.execute(
        "UPDATE cards SET status='unused' WHERE card_key=?", (req.card_key,)
    )
    await db.commit()
    return LicenseResponse(code=200, msg="解绑成功，用户可用此卡密重新激活")
