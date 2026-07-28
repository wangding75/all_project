"""瘦客户端桌面入口（方案 2）。

默认 CLIENT_MODE=thin：
  - 不内嵌服务端 / 不跑 Frida / 不含平台适配
  - 仅打开 WebView，连 API_BASE 上的服务端 /ui/

开发一体演示可用 CLIENT_MODE=embedded（本机拉起 uvicorn，仅本地调试）。
"""

from __future__ import annotations

import logging
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import webview

# ---------------------------------------------------------------------------
# 路径：client/desktop/main.py → repo root = parents[2]
# ---------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    _MEIPASS = sys._MEIPASS  # type: ignore[attr-defined]
    sys.path.insert(0, _MEIPASS)
    REPO_ROOT = Path(sys.executable).resolve().parent
else:
    REPO_ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(REPO_ROOT / "server"))

# 客户端模式：thin（默认）| embedded（本机嵌服务，仅开发）
CLIENT_MODE = os.environ.get("CLIENT_MODE", "thin").strip().lower()
if CLIENT_MODE not in {"thin", "embedded"}:
    CLIENT_MODE = "thin"

# 远程/本机服务端根地址（瘦客户端主配置）
API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:8000").rstrip("/")

env_path = REPO_ROOT / ".env"
if not env_path.is_file() and CLIENT_MODE == "embedded":
    default_env = (
        "# 仅 embedded 本机嵌服务时使用；瘦客户端请配置 API_BASE\n"
        "API_KEY=dev-key-change-me\n"
        "HOST=127.0.0.1\n"
        "PORT=8000\n"
        "AUTH_MODE=dev\n"
    )
    env_path.write_text(default_env, encoding="utf-8")
    print(f"[INIT] 缺省配置文件已生成: {env_path}")

logs_dir = REPO_ROOT / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)
log_file = logs_dir / "desktop.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(str(log_file), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("client.desktop")


class WindowApi:
    def __init__(self) -> None:
        self._window: webview.Window | None = None
        self.is_maximized = False

    def bind(self, window: webview.Window) -> None:
        self._window = window

    def minimize(self) -> None:
        if self._window:
            self._window.minimize()

    def toggle_maximized(self) -> None:
        if self._window:
            if self.is_maximized:
                self._window.restore()
                self.is_maximized = False
            else:
                self._window.maximize()
                self.is_maximized = True

    def close(self) -> None:
        if self._window:
            self._window.destroy()
        print("[EXIT] 通过标题栏关闭按钮触发关闭程序。")
        os._exit(0)


def is_port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0


def wait_for_server_healthy(base: str, timeout: float = 15.0) -> bool:
    start_time = time.time()
    url = f"{base.rstrip('/')}/health"
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, socket.timeout, TimeoutError):
            pass
        time.sleep(0.2)
    return False


def start_embedded_server(host: str, port: int) -> None:
    """仅 CLIENT_MODE=embedded：本机嵌服务（开发用）。"""
    import uvicorn
    from app.main import app

    uvicorn.run(app, host=host, port=port, log_level="warning")


def main() -> None:
    api_base = API_BASE
    print(f"[CLIENT] mode={CLIENT_MODE} api_base={api_base}")
    print("[CLIENT] 本程序不含平台适配 / Frida；适配仅在服务端。")

    if CLIENT_MODE == "embedded":
        from app.config import get_settings

        settings = get_settings()
        host, port = settings.host, int(settings.port)
        # 本机健康检查用 loopback，避免 HOST=0.0.0.0 探测失败
        probe_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
        api_base = f"http://{probe_host}:{port}"

        if is_port_in_use(probe_host, port):
            print(f"[ERR] 端口冲突 {probe_host}:{port}，请改 .env 或使用 thin 模式连已有服务端。")
            sys.exit(1)

        settings.data_dir.mkdir(parents=True, exist_ok=True)
        settings.jobs_dir.mkdir(parents=True, exist_ok=True)
        settings.outputs_dir.mkdir(parents=True, exist_ok=True)

        print(f"[START] embedded 服务 {host}:{port} ...")
        t = threading.Thread(target=start_embedded_server, args=(host, port), daemon=True)
        t.start()
        print("[START] 等待 /health ...")
        if not wait_for_server_healthy(api_base, timeout=15.0):
            print("[ERR] 服务端启动超时。")
            sys.exit(1)
        print("[START] 服务端就绪。")
    else:
        # 瘦客户端：只检查远程服务是否可达（失败仍打开窗口，便于改设置，但会提示）
        if not wait_for_server_healthy(api_base, timeout=5.0):
            print(
                f"[WARN] 无法连接服务端 {api_base}/health。"
                "请确认服务端已部署，或设置环境变量 API_BASE。"
            )
        else:
            print(f"[START] 服务端可达: {api_base}")

    ui_url = f"{api_base.rstrip('/')}/ui/"
    print(f"[WINDOW] PyWebView → {ui_url}")
    api = WindowApi()
    window = webview.create_window(
        title="资源下载客户端",
        url=ui_url,
        width=1200,
        height=800,
        resizable=True,
        min_size=(900, 600),
        frameless=True,
        text_select=True,
        js_api=api,
    )
    api.bind(window)

    def on_closed() -> None:
        print("[EXIT] 窗口关闭。")
        os._exit(0)

    window.events.closed += on_closed
    webview.start()


if __name__ == "__main__":
    main()
