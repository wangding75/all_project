from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import init_db
from api import license, cards


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="闪现 License Server",
    description="商业授权服务端：卡密管理 · 激活鉴权 · 三方卡网发货接口",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(license.router)
app.include_router(cards.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "sx-license-server", "version": "1.0.0"}
