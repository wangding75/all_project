"""桌面启动入口：在后台线程拉起 uvicorn，并在主线程中通过 pywebview 打开独立的桌面应用窗口。"""

from __future__ import annotations

import os
import sys
import time
import socket
import threading
import urllib.request
import urllib.error
import webview
from pathlib import Path

# 获取安装根目录 / 仓库根目录
if getattr(sys, "frozen", False):
    # PyInstaller 运行态
    _MEIPASS = sys._MEIPASS
    sys.path.insert(0, _MEIPASS)
    REPO_ROOT = Path(sys.executable).resolve().parent
else:
    # 源码开发态
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
    REPO_ROOT = Path(__file__).resolve().parents[1]

# [Note] 锁定加载顺序：必须先创建 .env 配置文件，再加载 get_settings 配置对象，
# 否则会因为 lru_cache 导致首次运行读取不到新生成的 .env
env_path = REPO_ROOT / ".env"
if not env_path.is_file():
    default_env = (
        "# 服务端密钥鉴权配置\n"
        "API_KEY=dev-key-change-me\n"
        "HOST=127.0.0.1\n"
        "PORT=8000\n"
    )
    env_path.write_text(default_env, encoding="utf-8")
    print(f"[INIT] 缺省配置文件已生成: {env_path}")

# 日志重定向：在打包或无黑框模式下将日志输出至 logs/desktop.log
logs_dir = REPO_ROOT / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)
log_file = logs_dir / "desktop.log"

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(str(log_file), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

from app.config import get_settings
from app.main import app


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


def start_server(host: str, port: int) -> None:
    import uvicorn
    # 降低日志级别以减少控制台的垃圾输出，突出应用提示
    uvicorn.run(app, host=host, port=port, log_level="warning")


def is_port_in_use(host: str, port: int) -> bool:
    """探测端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0


def wait_for_server_healthy(host: str, port: int, timeout: float = 15.0) -> bool:
    """轮询检测服务端 /health 端点是否就绪"""
    start_time = time.time()
    url = f"http://{host}:{port}/health"
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, socket.timeout):
            pass
        time.sleep(0.2)
    return False


def main() -> None:
    settings = get_settings()

    # 1. 检测端口冲突
    if is_port_in_use(settings.host, settings.port):
        print(f"[ERR] 端口冲突！地址 {settings.host}:{settings.port} 已被占用，请修改 .env 配置文件。")
        sys.exit(1)

    # 自动创建必要的数据与下载目录
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.jobs_dir.mkdir(parents=True, exist_ok=True)
    settings.outputs_dir.mkdir(parents=True, exist_ok=True)

    print(f"[START] 数据存储路径: {settings.data_dir}")
    print(f"[START] 正在后台启动中转服务端 {settings.host}:{settings.port} ...")

    # 2. 启动后台 uvicorn 服务线程
    t = threading.Thread(
        target=start_server,
        args=(settings.host, settings.port),
        daemon=True,
    )
    t.start()

    # 3. 轮询检测健康状态，等待就绪
    print("[START] 正在等待服务端健康检查响应...")
    if not wait_for_server_healthy(settings.host, settings.port, timeout=15.0):
        print("[ERR] 服务端启动超时！健康检查未通过，程序退出。")
        sys.exit(1)
    print("[START] 服务端已就绪，状态 OK。")

    ui_url = f"http://{settings.host}:{settings.port}/ui/"

    # 4. 初始化独立无边框桌面窗口，绑定 API 实例到 js_api 参数中
    print(f"[WINDOW] 正在使用 PyWebView 创建窗口: {ui_url}")
    api = WindowApi()
    window = webview.create_window(
        title="全能短剧/小说资源下载器",
        url=ui_url,
        width=1200,
        height=800,
        resizable=True,
        min_size=(900, 600),
        frameless=True,  # 开启无边框，启用定制的 app-titlebar
        text_select=True,
        js_api=api,      # 按 PyWebView 约定在此处传入 js_api 实例
    )

    api.bind(window)

    # 5. 注册窗口关闭事件回调
    def on_closed():
        print("[EXIT] 窗口被系统/用户关闭，退出后台服务。")
        os._exit(0)

    window.events.closed += on_closed

    # 6. 启动 GUI 循环
    webview.start()


if __name__ == "__main__":
    main()
