"""FastAPI 入口。"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api import api_router
from app.config import get_settings
from app.sign_pool import SignPoolUnavailableError


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    settings = get_settings()
    if settings.workers > 1:
        raise RuntimeError(
            f"本服务端仅支持单进程/单 Worker 模式运行 (WORKERS=1)，当前配置 WORKERS={settings.workers}"
        )

    # Resolve the named MuMu instance before any agent/App bootstrap. This is
    # fail-closed: a stale endpoint or ambiguous instance must stop startup.
    import os

    discovered_device = None
    if settings.platform_probe_on_startup or settings.fanqie_probe_on_startup:
        from platforms.device_discovery import resolve_rd_test_device

        discovered_device = resolve_rd_test_device(force=True, settings=settings)
        os.environ["RD_TEST_INSTANCE_NAME"] = discovered_device.instance_name
        os.environ["RD_TEST_ADB_SERIAL"] = discovered_device.serial

    # 同步到环境变量，供 vendor/hongguo 等上游模块读取（它们读 ADB / ADB_DEVICE，不是 ADB_PATH）
    if settings.adb_path:
        os.environ.setdefault("ADB", settings.adb_path)
        os.environ["ADB"] = settings.adb_path
    if discovered_device:
        os.environ["ADB_DEVICE"] = discovered_device.serial
    elif settings.adb_device:
        os.environ["ADB_DEVICE"] = settings.adb_device
    if settings.frida_host:
        os.environ["FRIDA_HOST"] = settings.frida_host

    settings.data_dir.mkdir(parents=True, exist_ok=True)

    # 初始化 SQLite 数据库
    from app.db import init_db
    init_db()

    # E3 生产安全默认检查：若配置违规则直接抛错阻断进程启动
    from app.security_boot import assert_production_secrets
    assert_production_secrets(settings)

    # License SDK is an application-lifetime dependency.  Routers obtain this
    # gateway through DI; they never construct a client per request.
    from app.license_gateway import initialize_license_gateway

    license_gateway = initialize_license_gateway(settings)
    _app.state.license_gateway = license_gateway
    if not license_gateway.configured:
        logging.warning(
            "License Service 未配置或配置无效；受保护业务将 fail-closed: error_code=%s",
            license_gateway.config_error or "UNKNOWN",
        )
        from app.security_boot import is_loopback_host

        if not is_loopback_host(settings.host):
            raise RuntimeError(
                "🚫 [T06 生产安全阻断] License Service SDK 配置无效，"
                "生产服务拒绝启动；请检查 RD Service Credential 与 TLS 配置。"
            )

    if settings.sign_pool_enabled:
        from app.sign_pool import get_sign_pool

        get_sign_pool()
        logging.info("签名节点池已启用 (SIGN_POOL_ENABLED=True)")

    # 多平台设备运行时：共享 Frida agent + 番茄/红果 App（可自启）
    runtime_bootstrapped = False
    if settings.platform_probe_on_startup or settings.fanqie_probe_on_startup:
        try:
            from platforms.runtime import bootstrap_on_startup

            bootstrap_on_startup()
            runtime_bootstrapped = True
        except RuntimeError:
            raise
        except Exception as exc:
            logging.warning("平台运行时探测异常（不阻断启动）: %s", exc)

    # 配置/依赖完整性（文件级：fanqie_config、hongguo_config、vendor 等）
    # Must run after the RD App/agent bootstrap so Fanqie session metadata can
    # be rebuilt on a clean state.
    try:
        from platforms.readiness import bootstrap_config_on_startup

        bootstrap_config_on_startup(recover_fanqie=runtime_bootstrapped)
    except Exception as exc:
        logging.warning("配置完整性检查异常（不阻断启动）: %s", exc)

    # 仅在启用运行时探测时汇总 ADB/Frida 状态；关闭开关必须保证完全离线启动。
    if settings.platform_probe_on_startup or settings.fanqie_probe_on_startup:
        try:
            from platforms.readiness import build_health_report, log_startup_readiness
            from platforms.runtime import probe_all_runtimes

            rt = probe_all_runtimes(try_start_agent=False, try_start_apps=False)
            full = build_health_report(include_runtime=True, runtime_report=rt)
            log_startup_readiness(full)
        except Exception as exc:
            logging.warning("启动健康汇总失败: %s", exc)

    yield
    logging.info("服务端收到退出信号，开始执行优雅关机流程...")
    from app.license_gateway import close_license_gateway

    close_license_gateway()


app = FastAPI(
    title="Resource Download Relay",
    version=__version__,
    description="MVP-1 中转服务端：番茄/红果下载链路（脚本与 UI 验收）",
    lifespan=lifespan,
)


@app.middleware("http")
async def track_request_metrics(request: Request, call_next):
    from app.logger import metrics_tracker

    metrics_tracker.inc_request()
    return await call_next(request)


@app.exception_handler(SignPoolUnavailableError)
async def sign_pool_unavailable_exception_handler(_request: Request, exc: SignPoolUnavailableError):
    return JSONResponse(
        status_code=503,
        content={"detail": exc.message},
    )


app.include_router(api_router)


# 智能定位 UI 静态资源路径
if getattr(sys, "frozen", False):
    # PyInstaller 仍将 UI 打包为 bundle 内 ui/（见 scripts/build_exe.py）
    UI_DIR = Path(sys._MEIPASS) / "ui"
else:
    # 源码：方案 2 客户端在 client/ui；兼容旧路径 ui/
    _repo = Path(__file__).resolve().parent.parent.parent
    _candidates = (_repo / "client" / "ui", _repo / "ui")
    UI_DIR = next((p for p in _candidates if p.is_dir()), _candidates[0])

if UI_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(UI_DIR), html=True), name="ui")


@app.get("/")
async def root():
    """首页跳到 /ui/，保证 styles.css / app.js 相对路径可解析。

    直接 FileResponse(index.html) 时，浏览器会向 /styles.css 请求，
    而静态资源只挂在 /ui/ 下，导致「CSS 样式丢失」。
    """
    if UI_DIR.exists() and (UI_DIR / "index.html").is_file():
        return RedirectResponse(url="/ui/", status_code=307)
    return {
        "service": "resource-download-relay",
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
        "ui": "/ui/",
    }


# 兼容旧书签：/styles.css、/app.js → /ui/...
@app.get("/styles.css")
async def legacy_styles():
    path = UI_DIR / "styles.css"
    if path.is_file():
        return FileResponse(path, media_type="text/css")
    return JSONResponse({"detail": "styles.css not found"}, status_code=404)


@app.get("/app.js")
async def legacy_app_js():
    path = UI_DIR / "app.js"
    if path.is_file():
        return FileResponse(path, media_type="application/javascript")
    return JSONResponse({"detail": "app.js not found"}, status_code=404)

