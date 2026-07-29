"""瘦客户端桌面入口（方案 2）。

默认 CLIENT_MODE=thin：
  - 不内嵌服务端 / 不跑 Frida / 不含平台适配
  - 仅打开 WebView，连 API_BASE 上的服务端 /ui/

开发一体演示可用 CLIENT_MODE=embedded（本机拉起 uvicorn，仅本地调试）。
"""

from __future__ import annotations

import html
import hashlib
import json
import logging
import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import webview

try:
    from client.desktop.version import CLIENT_VERSION
except ImportError:
    from version import CLIENT_VERSION

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


def is_secure_api_base(base: str) -> bool:
    """远程服务必须使用 HTTPS；仅本机环回地址允许 HTTP。"""
    try:
        parsed = urllib.parse.urlparse(base)
    except ValueError:
        return False
    if parsed.scheme == "https":
        return bool(parsed.hostname)
    return parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}


def _safe_filename(name: str) -> str:
    """生成安全的 Windows 本地文件名，阻止路径穿越和非法字符。"""
    clean = Path(name or "download.bin").name.strip()
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", clean)
    clean = clean.rstrip(" .")
    return clean or "download.bin"


class WindowApi:
    def __init__(self, api_base: str) -> None:
        self._window: webview.Window | None = None
        self.is_maximized = False
        self.api_base = api_base.rstrip("/")
        self._download_dir = Path.home() / "Downloads" / "ResourceDownloader"
        self._local_files: dict[str, Path] = {}
        local_app_data = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / ".resource-downloader"))
        self._preferences_path = local_app_data / "ResourceDownloader" / "client.json"
        self._updates_dir = local_app_data / "ResourceDownloader" / "updates"
        self._install_id = ""
        try:
            if self._preferences_path.is_file():
                payload = json.loads(self._preferences_path.read_text(encoding="utf-8"))
                saved_dir = str(payload.get("download_directory") or "").strip()
                if saved_dir:
                    self._download_dir = Path(saved_dir).expanduser().resolve()
                self._install_id = str(payload.get("install_id") or "").strip()
        except Exception:
            log.warning("无法读取客户端本地偏好，将使用默认下载目录")
        if not self._install_id:
            import uuid

            self._install_id = uuid.uuid4().hex
            self._persist_preferences(remember_directory=False)

    def _persist_preferences(self, *, remember_directory: bool) -> None:
        self._preferences_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"install_id": self._install_id}
        if remember_directory:
            payload["download_directory"] = str(self._download_dir)
        temp_path = self._preferences_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        temp_path.replace(self._preferences_path)

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

    def get_download_directory(self) -> dict[str, object]:
        return {"success": True, "path": str(self._download_dir)}

    def get_runtime_info(self) -> dict[str, object]:
        return {
            "success": True,
            "api_base": self.api_base,
            "download_directory": str(self._download_dir),
            "client_version": CLIENT_VERSION,
            "install_id": self._install_id,
        }

    def choose_download_directory(self, remember: bool = True) -> dict[str, object]:
        if not self._window:
            return {"success": False, "message": "窗口尚未就绪"}
        try:
            selected = self._window.create_file_dialog(
                webview.FOLDER_DIALOG,
                directory=str(self._download_dir.parent),
            )
            if not selected:
                return {"success": False, "cancelled": True, "message": "已取消选择"}
            chosen = Path(selected[0]).expanduser().resolve()
            chosen.mkdir(parents=True, exist_ok=True)
            self._download_dir = chosen
            self._persist_preferences(remember_directory=bool(remember))
            return {"success": True, "path": str(chosen)}
        except Exception as exc:
            log.exception("选择本地下载目录失败")
            return {"success": False, "message": f"选择目录失败: {exc}"}

    def set_remember_download_directory(self, remember: bool) -> dict[str, object]:
        try:
            self._persist_preferences(remember_directory=bool(remember))
            return {"success": True, "remember": bool(remember)}
        except Exception as exc:
            return {"success": False, "message": f"保存目录偏好失败: {exc}"}

    def download_update(self, url: str, sha256: str = "") -> dict[str, object]:
        """安全下载更新安装包；仅接受 HTTPS 并校验服务端发布的 SHA-256。"""
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme != "https" or not parsed.hostname:
                return {"success": False, "message": "更新地址必须使用 HTTPS"}
            name = _safe_filename(Path(parsed.path).name or "ResourceDownloader-Setup.exe")
            if not name.lower().endswith(".exe"):
                return {"success": False, "message": "更新包必须是 Windows EXE 安装程序"}
            self._updates_dir.mkdir(parents=True, exist_ok=True)
            target = self._updates_dir / name
            partial = target.with_suffix(target.suffix + ".part")
            digest = hashlib.sha256()
            request = urllib.request.Request(url, headers={"User-Agent": f"ResourceDownloader/{CLIENT_VERSION}"})
            with urllib.request.urlopen(request, timeout=300) as response, partial.open("wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
            actual = digest.hexdigest().lower()
            expected = str(sha256 or "").strip().lower()
            if not expected or actual != expected:
                partial.unlink(missing_ok=True)
                return {"success": False, "message": "更新包 SHA-256 校验失败"}
            partial.replace(target)
            return {"success": True, "path": str(target), "sha256": actual}
        except Exception as exc:
            log.exception("下载客户端更新失败")
            return {"success": False, "message": f"下载更新失败: {exc}"}

    def install_update(self, path: str, mandatory: bool = False) -> dict[str, object]:
        """启动已校验安装包，安装器负责替换旧版本。"""
        try:
            target = Path(path).resolve()
            updates_root = self._updates_dir.resolve()
            if not target.is_file() or not target.is_relative_to(updates_root):
                return {"success": False, "message": "更新包路径无效"}
            args = [str(target), "/SP-", "/SILENT", "/NORESTART"]
            subprocess.Popen(args, cwd=str(target.parent))
            if self._window:
                self._window.destroy()
            threading.Timer(0.5, lambda: os._exit(0)).start()
            return {"success": True, "mandatory": bool(mandatory)}
        except Exception as exc:
            log.exception("启动客户端更新失败")
            return {"success": False, "message": f"启动更新失败: {exc}"}

    def download_file(
        self,
        file_id: str,
        filename: str,
        access_token: str = "",
        api_key: str = "",
    ) -> dict[str, object]:
        """从服务端鉴权下载文件到客户机，使用 .part + replace 原子落盘。"""
        if not file_id or file_id in {".", "/", "\\"}:
            return {"success": False, "message": "无效的文件标识"}

        encoded = "/".join(urllib.parse.quote(part, safe="") for part in file_id.replace("\\", "/").split("/"))
        url = f"{self.api_base}/v1/files/{encoded}"
        headers: dict[str, str] = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        elif api_key:
            headers["X-API-Key"] = api_key

        normalized_parts = [part for part in file_id.replace("\\", "/").split("/") if part]
        job_folder = _safe_filename(normalized_parts[0]) if len(normalized_parts) > 1 else ""
        target_dir = self._download_dir / job_folder if job_folder else self._download_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / _safe_filename(filename or Path(file_id).name)
        partial = target.with_name(f"{target.name}.part")
        try:
            request = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(request, timeout=300) as response, partial.open("wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
            partial.replace(target)
            resolved = target.resolve()
            self._local_files[file_id] = resolved
            return {
                "success": True,
                "path": str(resolved),
                "size": resolved.stat().st_size,
                "message": f"已下载到本机: {resolved}",
            }
        except urllib.error.HTTPError as exc:
            partial.unlink(missing_ok=True)
            detail = f"HTTP {exc.code}"
            try:
                payload = json.loads(exc.read().decode("utf-8", errors="replace"))
                detail = str(payload.get("detail") or detail)
            except Exception:
                pass
            return {"success": False, "message": f"服务端拒绝下载: {detail}"}
        except Exception as exc:
            partial.unlink(missing_ok=True)
            log.exception("客户端下载失败 file_id=%s", file_id)
            return {"success": False, "message": f"下载到本机失败: {exc}"}

    def open_local_file(self, file_id: str, action: str = "play") -> dict[str, object]:
        path = self._local_files.get(file_id)
        if path is None or not path.is_file():
            return {"success": False, "message": "本机文件不存在，请先下载"}
        try:
            if action == "folder":
                subprocess_args = ["explorer.exe", f'/select,"{path}"']
                import subprocess

                subprocess.Popen(subprocess_args)
            else:
                os.startfile(str(path))
            return {"success": True, "path": str(path)}
        except Exception as exc:
            log.exception("打开本机文件失败 file_id=%s", file_id)
            return {"success": False, "message": f"打开本机文件失败: {exc}"}

    def open_download_directory(self) -> dict[str, object]:
        try:
            self._download_dir.mkdir(parents=True, exist_ok=True)
            os.startfile(str(self._download_dir))
            return {"success": True, "path": str(self._download_dir)}
        except Exception as exc:
            log.exception("打开本机下载目录失败")
            return {"success": False, "message": f"打开下载目录失败: {exc}"}


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
        if not is_secure_api_base(api_base):
            message = (
                "为保护账号、卡密和下载内容，远程服务端必须使用 HTTPS。\n"
                f"当前地址不安全: {api_base}\n\n"
                "请联系管理员配置 HTTPS，或仅在本机使用 http://127.0.0.1。"
            )
            log.error(message.replace("\n", " "))
            webview.create_window(
                title="资源下载客户端 - 安全配置错误",
                html=f"<main style='font-family:sans-serif;padding:32px'><h2>无法连接不安全的服务端</h2>"
                f"<p>{html.escape(message).replace(chr(10), '<br>')}</p></main>",
                width=720,
                height=420,
            )
            webview.start()
            return
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
    api = WindowApi(api_base)
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
