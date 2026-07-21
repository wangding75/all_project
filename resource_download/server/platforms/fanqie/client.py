"""番茄小说独立的 App API 客户端（包含签名、拉章等，完全独立运行且不依赖红果模块）"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlparse

import warnings
import requests
import urllib3


HERE = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]
CFG_PATH = REPO_ROOT / "data" / "config" / "fanqie_config.json"

_CFG: dict[str, Any] = {}
_CFG_LOCK = threading.Lock()


def load_config() -> dict[str, Any]:
    global _CFG
    with _CFG_LOCK:
        if not _CFG:
            if not CFG_PATH.is_file():
                # 默认保底配置，防止没有配置文件时崩溃
                _CFG = {
                    "api_host": "api5-normal-sinfonlinea.fqnovel.com",
                    "base_query": {
                        "iid": "3612332575192992",
                        "device_id": "3612332575188896",
                        "aid": "1967",
                        "app_name": "novelread",
                        "version_code": "70533",
                        "version_name": "7.0.5.33",
                        "device_platform": "android",
                        "os": "android"
                    },
                    "session_headers": {
                        "user-agent": "com.dragon.read/70533 (Linux; U; Android 15; zh_CN;tt-ok/3.12.13.20)",
                        "sdk-version": "2"
                    }
                }
            else:
                _CFG = json.loads(CFG_PATH.read_text(encoding="utf-8"))
        return _CFG


class FanqieSignOracle:
    """番茄独立的 Frida 签名预言机"""
    def __init__(self) -> None:
        self.session = None
        self.script = None
        self._lock = threading.RLock()

    def init_frida(self) -> None:
        import frida  # type: ignore
        from app.config import get_settings
        settings = get_settings()
        adb = os.environ.get("ADB", settings.adb_path)
        dev = os.environ.get("ADB_DEVICE", settings.adb_device)
        frida_host = os.environ.get("FRIDA_HOST", settings.frida_host)
        pkg = os.environ.get("FANQIE_PKG", settings.fanqie_pkg)

        # 确保 ADB 已连接
        subprocess.run([adb, "connect", dev], capture_output=True)
        pid_out = subprocess.run(
            [adb, "-s", dev, "shell", "pidof", pkg],
            capture_output=True,
            text=True,
        ).stdout.strip()
        if not pid_out:
            # 尝试启动 App
            subprocess.run(
                [adb, "-s", dev, "shell", "monkey", "-p", pkg,
                 "-c", "android.intent.category.LAUNCHER", "1"],
                capture_output=True,
            )
            time.sleep(8)
            pid_out = subprocess.run(
                [adb, "-s", dev, "shell", "pidof", pkg],
                capture_output=True,
                text=True,
            ).stdout.strip()
        if not pid_out:
            raise RuntimeError(f"无法启动/获取番茄小说进程 {pkg}，请确认模拟器已开启且已打开该 App")
        
        pid = int(pid_out.split()[0])
        
        # 检查并启动 frida-server
        ps = subprocess.run([adb, "-s", dev, "shell", "ps", "-A"], capture_output=True, text=True).stdout
        if "sys_hlpd" not in ps and "frida-server" not in ps:
            subprocess.run([adb, "-s", dev, "shell", "/data/local/tmp/frida-server -D &"], capture_output=True)
            time.sleep(2)
            
        subprocess.run([adb, "-s", dev, "forward", "tcp:27042", "tcp:27042"], capture_output=True)
        frida_dev = frida.get_device_manager().add_remote_device(frida_host)
        self.session = frida_dev.attach(pid)

        
        js_path = HERE / "oracle_sign.js"
        self.script = self.session.create_script(js_path.read_text(encoding="utf-8"))
        self.script.load()

    def sign(self, url: str, headers: dict[str, str]) -> dict[str, str]:
        with self._lock:
            if not self.script:
                self.init_frida()
            assert self.script is not None
            return self.script.exports_sync.sign(url, headers)

    def close(self) -> None:
        with self._lock:
            if self.session:
                try:
                    self.session.detach()
                except Exception:
                    pass
                self.session = None
                self.script = None


_oracle = None
_oracle_lock = threading.RLock()


def get_oracle() -> FanqieSignOracle:
    global _oracle
    if _oracle is None:
        with _oracle_lock:
            if _oracle is None:
                _oracle = FanqieSignOracle()
    return _oracle


def sign(url: str, headers: dict[str, str]) -> dict[str, str]:
    from app.config import get_settings

    if get_settings().sign_pool_enabled:
        from app.sign_pool import sign_via_pool

        return sign_via_pool("fanqie_sign", url, headers)
    return get_oracle().sign(url, headers)


def refresh_session() -> None:
    """从运行中的 App 重新捕获最新的 token (类似于红果的 refresh)"""
    # 这里通过抓取脚本或运行期间自动刷新，可作为占位
    pass


def build_url(path: str, extra: dict[str, str] | None = None) -> str:
    cfg = load_config()
    q = dict(cfg["base_query"])
    if extra:
        q.update(extra)
    q["_rticket"] = str(int(time.time() * 1000))
    qs = "&".join(f"{k}={requests.utils.quote(str(v), safe='')}" for k, v in q.items())
    return f"https://{cfg['api_host']}{path}?{qs}"


def api_once(method: str, path: str, body: dict | None = None, extra_query: dict[str, str] | None = None, signed: bool = True) -> dict[str, Any]:
    cfg = load_config()
    url = build_url(path, extra_query)
    headers = dict(cfg["session_headers"])
    headers["content-type"] = "application/json; charset=utf-8"
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        headers["x-ss-stub"] = hashlib.md5(data).hexdigest().upper()
    if signed:
        headers.update(sign(url, headers))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)
        r = requests.request(method, url, data=data, headers=headers, verify=False, timeout=30)
    r.raise_for_status()
    return r.json()



def api(method: str, path: str, body: dict | None = None, extra_query: dict[str, str] | None = None, max_retries: int = 3, signed: bool = True) -> dict[str, Any]:
    last = None
    for attempt in range(max_retries):
        try:
            return api_once(method, path, body, extra_query, signed=signed)
        except Exception as e:
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise last if last else RuntimeError("API request failed")


# --- 业务 API ---

def search(query: str, max_items: int = 20) -> list[dict[str, Any]]:
    """调用番茄 App 搜索接口"""
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    offset = 0
    passback = ""
    search_id = ""
    for _ in range(5):  # 翻页限制
        q = {
            "query": query,
            "tab_name": "feed",
            "search_source": "1",
            "offset": str(offset),
            "count": "20",
            "use_correct": "true"
        }
        if passback:
            q["passback"] = passback
        if search_id:
            q["search_id"] = search_id
            
        j = api("GET", "/reading/bookapi/search/tab/v", extra_query=q)
        tabs = j.get("search_tabs") or []
        if not tabs:
            break
        tab = tabs[0]
        data = tab.get("data") or []
        for cell in data:
            bid = cell.get("book_id") or cell.get("search_result_id")
            if not bid:
                continue
            bid = str(bid)
            if bid in seen:
                continue
            seen.add(bid)
            results.append({
                "book_id": bid,
                "title": cell.get("book_name") or cell.get("title") or "",
                "author": cell.get("author") or "",
                "cover": cell.get("cover") or "",
                "desc": cell.get("abstract") or cell.get("desc") or ""
            })
            if len(results) >= max_items:
                break
        if len(results) >= max_items or not tab.get("has_more"):
            break
        offset = tab.get("next_offset") or (offset + 20)
        passback = tab.get("passback") or ""
        search_id = tab.get("search_id") or ""
    return results


def get_directory(book_id: str) -> tuple[list[str], dict[str, Any]]:
    """拉取目录章节 IDs"""
    last = {}
    for path in (
        "/reading/bookapi/directory/all_items/v",
        "/reading/bookapi/directory/all_infos/v",
    ):
        try:
            j = api("GET", path, extra_query={"book_id": book_id})
            last = j
            
            # 遍历结构提取 item_id
            def walk_item_ids(obj, out: list[str]) -> list[str]:
                if isinstance(obj, dict):
                    if "item_id" in obj:
                        v = obj["item_id"]
                        if v is not None and str(v).isdigit():
                            out.append(str(v))
                    for val in obj.values():
                        walk_item_ids(val, out)
                elif isinstance(obj, list):
                    for val in obj:
                        walk_item_ids(val, out)
                return out

            ids = walk_item_ids(j, [])
            # 去重保序
            seen = set()
            uniq = []
            for item_id in ids:
                if item_id not in seen:
                    seen.add(item_id)
                    uniq.append(item_id)
            if uniq:
                return uniq, j
        except Exception as e:
            print(f"Directory fetch fail ({path}): {e}")
    return [], last


def fetch_full(book_id: str, item_id: str) -> dict[str, Any]:
    """拉取章节加密正文数据"""
    return api(
        "GET",
        "/reading/reader/full/v",
        extra_query={"item_id": item_id, "book_id": book_id, "novel_id": book_id},
    )
