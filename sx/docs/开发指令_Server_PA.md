# 开发指令 — 服务端 P-A 商业授权

| 项 | 内容 |
|----|------|
| 指令版本 | v1.0 |
| 日期 | 2026-07-21 |
| 技术栈 | Python 3.11+ · FastAPI · SQLite · Uvicorn |
| 目录 | `server/` （仓库根目录下） |
| 依据 | [29_商业授权技术方案.md](./29_商业授权技术方案.md) |

---

## 一、项目结构

```
server/
├── main.py                  # FastAPI 入口
├── config.py                # 环境变量配置
├── database.py              # SQLite 连接与初始化
├── models/
│   ├── card.py              # 卡密数据模型
│   └── activation.py        # 激活记录模型
├── api/
│   ├── license.py           # 客户端鉴权接口（/api/license/*）
│   └── cards.py             # 发货 Webhook 接口（/api/cards/*）
├── core/
│   ├── auth.py              # Token 生成/验签
│   ├── sign.py              # 请求签名校验
│   └── card_gen.py          # 卡密批量生成
├── requirements.txt
├── .env.example             # 环境变量模板（提交 Git）
├── .env                     # 真实配置（不提交 Git）
└── README.md                # 部署说明
```

---

## 二、执行步骤

### Step 1 — 创建项目骨架

在仓库根目录下新建 `server/` 文件夹，创建以下文件：

---

#### `server/requirements.txt`

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-dotenv==1.0.1
pydantic==2.7.1
aiosqlite==0.20.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.27.0
```

---

#### `server/.env.example`

```env
# 服务端密钥（部署时替换为随机强密码）
SERVER_SECRET=CHANGE_ME_USE_STRONG_RANDOM_SECRET_32CHARS

# 卡网 Webhook 鉴权密钥
CARDNET_WEBHOOK_SECRET=CHANGE_ME_CARDNET_SECRET

# 数据库路径
DATABASE_URL=./sx_license.db

# 管理员 API Key（管理后台接口用）
ADMIN_API_KEY=CHANGE_ME_ADMIN_KEY

# 监听端口
PORT=8000
```

---

#### `server/config.py`

```python
from dotenv import load_dotenv
import os

load_dotenv()

SERVER_SECRET       = os.getenv("SERVER_SECRET", "dev_secret_change_in_prod")
CARDNET_WEBHOOK_SECRET = os.getenv("CARDNET_WEBHOOK_SECRET", "dev_webhook_secret")
DATABASE_URL        = os.getenv("DATABASE_URL", "./sx_license.db")
ADMIN_API_KEY       = os.getenv("ADMIN_API_KEY", "dev_admin_key")
PORT                = int(os.getenv("PORT", "8000"))

# Token 有效期校验宽限（秒），防止网络抖动导致误判
TOKEN_CLOCK_SKEW_SEC = 60
```

---

#### `server/database.py`

```python
import aiosqlite
from config import DATABASE_URL

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS cards (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    card_key    TEXT UNIQUE NOT NULL,
    duration_days INTEGER NOT NULL DEFAULT 30,  -- -1 = 永久
    status      TEXT NOT NULL DEFAULT 'unused', -- unused/activated/revoked
    created_at  INTEGER NOT NULL,
    batch_id    TEXT
);

CREATE TABLE IF NOT EXISTS activations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    card_key        TEXT NOT NULL,
    device_id       TEXT NOT NULL,
    activated_at    INTEGER NOT NULL,
    expire_at       INTEGER NOT NULL,           -- Unix ms；-1 = 永久
    is_active       INTEGER NOT NULL DEFAULT 1, -- 1=有效；0=已解绑
    UNIQUE(card_key)                            -- 一卡绑一设备
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
```

---

#### `server/core/card_gen.py`

```python
import random
import string
import time
import aiosqlite
from config import DATABASE_URL

def _rand_segment(n=4) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

def generate_card_key() -> str:
    """生成格式：SX-XXXX-XXXX-XXXX"""
    return f"SX-{_rand_segment()}-{_rand_segment()}-{_rand_segment()}"

async def create_cards_batch(duration_days: int, count: int, batch_id: str = None) -> list[str]:
    """批量生成并写入卡密，返回卡密列表"""
    now = int(time.time() * 1000)
    cards = []
    async with aiosqlite.connect(DATABASE_URL) as db:
        for _ in range(count):
            while True:
                key = generate_card_key()
                try:
                    await db.execute(
                        "INSERT INTO cards (card_key, duration_days, created_at, batch_id) VALUES (?,?,?,?)",
                        (key, duration_days, now, batch_id)
                    )
                    cards.append(key)
                    break
                except Exception:
                    continue  # 重复则重生成
        await db.commit()
    return cards
```

---

#### `server/core/auth.py`

```python
import hashlib
import hmac
import time
import json
import base64
from config import SERVER_SECRET, TOKEN_CLOCK_SKEW_SEC

def _b64(data: str) -> str:
    return base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")

def _sign(payload_b64: str) -> str:
    return hmac.new(
        SERVER_SECRET.encode(), payload_b64.encode(), hashlib.sha256
    ).hexdigest()

def create_token(card_key: str, device_id: str, expire_at: int) -> str:
    """
    生成 Token = base64(payload).signature
    payload = { card_key, device_id, expire_at, issued_at }
    """
    payload = {
        "card_key":  card_key,
        "device_id": device_id,
        "expire_at": expire_at,
        "issued_at": int(time.time() * 1000)
    }
    payload_b64 = _b64(json.dumps(payload, separators=(',', ':')))
    sig = _sign(payload_b64)
    return f"{payload_b64}.{sig}"

def verify_token(token: str, device_id: str) -> dict | None:
    """
    验证 Token 合法性
    返回 payload dict（含 expire_at）；失败返回 None
    """
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig = parts
        # 验签
        expected_sig = _sign(payload_b64)
        if not hmac.compare_digest(sig, expected_sig):
            return None
        # 解码 payload
        padded = payload_b64 + "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode())
        # 校验设备
        if payload.get("device_id") != device_id:
            return None
        # 校验过期（-1 = 永久）
        expire_at = payload.get("expire_at", 0)
        if expire_at != -1:
            now_ms = int(time.time() * 1000)
            if now_ms > expire_at + TOKEN_CLOCK_SKEW_SEC * 1000:
                return None
        return payload
    except Exception:
        return None
```

---

#### `server/core/sign.py`

```python
import hashlib
from fastapi import HTTPException

def verify_client_sign(card_key: str, device_id: str, sign: str, app_secret: str):
    """
    校验客户端请求签名
    规则：MD5(card_key + device_id + app_secret).upper()
    """
    raw = card_key + device_id + app_secret
    expected = hashlib.md5(raw.encode()).hexdigest().upper()
    if sign.upper() != expected:
        raise HTTPException(status_code=401, detail="签名验证失败")
```

---

#### `server/api/license.py`

```python
import time
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
import aiosqlite
from database import get_db
from core.auth import create_token, verify_token
from core.sign import verify_client_sign
from config import SERVER_SECRET

router = APIRouter(prefix="/api/license", tags=["license"])

# ── 请求/响应模型 ─────────────────────────────────

class ActivateRequest(BaseModel):
    card_key:  str
    device_id: str
    sign:      str          # MD5(card_key+device_id+app_secret).upper()

class LicenseResponse(BaseModel):
    code:    int
    msg:     str
    data:    dict | None = None

# ── 激活接口 ──────────────────────────────────────

@router.post("/activate", response_model=LicenseResponse)
async def activate(req: ActivateRequest, db: aiosqlite.Connection = Depends(get_db)):
    verify_client_sign(req.card_key, req.device_id, req.sign, SERVER_SECRET)

    # 查卡密
    async with db.execute("SELECT * FROM cards WHERE card_key=?", (req.card_key,)) as cur:
        card = await cur.fetchone()
    if not card:
        return LicenseResponse(code=400, msg="卡密不存在")
    if card["status"] == "revoked":
        return LicenseResponse(code=400, msg="卡密已作废")

    # 查激活记录
    async with db.execute(
        "SELECT * FROM activations WHERE card_key=?", (req.card_key,)
    ) as cur:
        activation = await cur.fetchone()

    now_ms = int(time.time() * 1000)

    if activation:
        # 已有激活记录
        if not activation["is_active"]:
            return LicenseResponse(code=400, msg="卡密已被解绑，请联系客服")
        if activation["device_id"] != req.device_id:
            return LicenseResponse(code=400, msg="该卡密已绑定其他设备")
        # 同设备重复激活：直接返回当前 Token
        token = create_token(req.card_key, req.device_id, activation["expire_at"])
        return LicenseResponse(code=200, msg="激活成功", data={
            "token": token,
            "expire_at": activation["expire_at"]
        })

    # 首次激活
    duration_days = card["duration_days"]
    expire_at = -1 if duration_days == -1 else now_ms + duration_days * 86400 * 1000

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
        "token": token,
        "expire_at": expire_at
    })

# ── 鉴权校验接口 ──────────────────────────────────

@router.get("/verify", response_model=LicenseResponse)
async def verify(
    device_id: str,
    authorization: str = Header(...),   # Bearer {token}
    db: aiosqlite.Connection = Depends(get_db)
):
    token = authorization.removeprefix("Bearer ").strip()
    payload = verify_token(token, device_id)
    if not payload:
        return LicenseResponse(code=401, msg="Token 无效或已过期",
                               data={"valid": False})

    # 再查库确认未被解绑
    async with db.execute(
        "SELECT is_active, expire_at FROM activations WHERE card_key=?",
        (payload["card_key"],)
    ) as cur:
        row = await cur.fetchone()
    if not row or not row["is_active"]:
        return LicenseResponse(code=401, msg="授权已失效",
                               data={"valid": False})

    return LicenseResponse(code=200, msg="授权有效", data={
        "valid": True,
        "expire_at": row["expire_at"]
    })

# ── 解绑接口（管理员发起）────────────────────────

class UnbindRequest(BaseModel):
    card_key:     str
    admin_api_key: str

@router.post("/unbind", response_model=LicenseResponse)
async def unbind(req: UnbindRequest, db: aiosqlite.Connection = Depends(get_db)):
    from config import ADMIN_API_KEY
    if req.admin_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="无权限")
    await db.execute(
        "UPDATE activations SET is_active=0 WHERE card_key=?", (req.card_key,)
    )
    await db.execute(
        "UPDATE cards SET status='unused' WHERE card_key=?", (req.card_key,)
    )
    await db.commit()
    return LicenseResponse(code=200, msg="解绑成功，用户可重新激活")
```

---

#### `server/api/cards.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from database import get_db
from core.card_gen import create_cards_batch
from config import CARDNET_WEBHOOK_SECRET, ADMIN_API_KEY
import aiosqlite

router = APIRouter(prefix="/api/cards", tags=["cards"])

# ── 三方卡网发货 Webhook ──────────────────────────

class DeliverRequest(BaseModel):
    order_id:   str
    product_id: str   # 对应卡密规格：如 "sx_30d" "sx_90d" "sx_perm"
    quantity:   int = 1

PRODUCT_DURATION_MAP = {
    "sx_7d":   7,
    "sx_30d":  30,
    "sx_90d":  90,
    "sx_365d": 365,
    "sx_perm": -1,   # 永久
}

@router.post("/deliver")
async def deliver(
    req: DeliverRequest,
    authorization: str = Header(...),
    db: aiosqlite.Connection = Depends(get_db)
):
    # 校验卡网 Webhook 密钥
    if authorization.removeprefix("Bearer ").strip() != CARDNET_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Webhook 密钥错误")

    duration_days = PRODUCT_DURATION_MAP.get(req.product_id)
    if duration_days is None:
        raise HTTPException(status_code=400, detail=f"未知商品 ID: {req.product_id}")

    cards = await create_cards_batch(
        duration_days=duration_days,
        count=req.quantity,
        batch_id=req.order_id
    )
    return {"code": 200, "cards": cards}

# ── 管理员批量生成卡密 ────────────────────────────

class GenRequest(BaseModel):
    duration_days: int          # -1=永久
    count:         int
    admin_api_key: str

@router.post("/generate")
async def generate(req: GenRequest, db: aiosqlite.Connection = Depends(get_db)):
    if req.admin_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="无权限")
    if req.count > 1000:
        raise HTTPException(status_code=400, detail="单次最多 1000 张")
    cards = await create_cards_batch(req.duration_days, req.count)
    return {"code": 200, "count": len(cards), "cards": cards}

# ── 管理员查询卡密状态 ────────────────────────────

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
        "card_key":     card_key,
        "status":       card["status"],
        "duration_days":card["duration_days"],
        "activation":   dict(act) if act else None
    }
```

---

#### `server/main.py`

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import init_db
from api import license, cards

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()          # 启动时建表
    yield

app = FastAPI(
    title="闪现 License Server",
    description="商业授权服务端：卡密管理 · 激活鉴权 · 三方卡网发货接口",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(license.router)
app.include_router(cards.router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "sx-license-server"}
```

---

#### `server/README.md`

```markdown
# 闪现授权服务端

## 快速启动

\`\`\`bash
cd server
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env           # 编辑 .env 填写密钥
uvicorn main:app --reload --port 8000
\`\`\`

## API 文档

启动后访问：http://localhost:8000/docs

## 核心接口

| 接口 | 调用方 | 说明 |
|------|--------|------|
| POST /api/license/activate | 客户端 | 激活卡密 |
| GET  /api/license/verify   | 客户端 | 鉴权校验 |
| POST /api/license/unbind   | 管理员 | 解绑设备 |
| POST /api/cards/deliver    | 三方卡网 Webhook | 发货取卡密 |
| POST /api/cards/generate   | 管理员 | 批量生成卡密 |
| GET  /api/cards/status/:key | 管理员 | 查卡密状态 |
```

---

### Step 2 — 本地环境搭建与首次运行

```powershell
cd D:\github\all_project\sx\server

# 创建虚拟环境
python -m venv venv
.\venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境配置
copy .env.example .env
# 编辑 .env，把所有 CHANGE_ME 替换为真实密钥

# 启动（热重载开发模式）
uvicorn main:app --reload --port 8000
```

**验收：** 访问 `http://localhost:8000/docs` 能看到 FastAPI 自动生成的 Swagger 文档。

---

### Step 3 — 接口联调验收

**生成测试卡密（30天）：**

```bash
curl -X POST http://localhost:8000/api/cards/generate \
  -H "Content-Type: application/json" \
  -d '{"duration_days":30,"count":3,"admin_api_key":"dev_admin_key"}'
```

**激活卡密（模拟客户端）：**

```python
import hashlib, requests

card_key  = "SX-XXXX-XXXX-XXXX"  # 上一步生成的
device_id = "test_device_abc123"
secret    = "dev_secret_change_in_prod"  # .env 里的 SERVER_SECRET
sign      = hashlib.md5((card_key + device_id + secret).encode()).hexdigest().upper()

resp = requests.post("http://localhost:8000/api/license/activate", json={
    "card_key": card_key,
    "device_id": device_id,
    "sign": sign
})
print(resp.json())
```

**鉴权校验：**

```bash
curl http://localhost:8000/api/license/verify?device_id=test_device_abc123 \
  -H "Authorization: Bearer <上一步返回的 token>"
```

---

### Step 4 — .gitignore 补充

在项目根 `.gitignore` 追加：

```
server/.env
server/sx_license.db
server/venv/
server/__pycache__/
server/**/__pycache__/
```

---

### Step 5 — 提交

```powershell
git add server/
git commit -m "feat(server): P-A license server - FastAPI + SQLite, activate/verify/unbind/deliver"
```

---

## 三、完成后同步

- `docs/10_Backlog.md`：P-A01 + P-A02 标为 `done`
- `docs/29_商业授权技术方案.md`：标注服务端已实现
- 下一步：客户端 `SxServerLicenseServer` 对接此服务端 `/activate` 和 `/verify`
