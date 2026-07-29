"""番茄小说独立的 App API 客户端。

签名 / 拉章仅依赖：
  - 模拟器内 **番茄** `com.dragon.read`（`FANQIE_PKG`）
  - 本机 Frida agent + `oracle_sign.js`（NetworkParams.tryAddSecurityFactor）

**不依赖** 红果 `com.phoenix.read`、vendor/hongguo 或红果签名预言机。
同一模拟器可同时运行红果与番茄两个 App。
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

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
    """番茄独立签名预言机：attach com.dragon.read，调用 NetworkParams.tryAddSecurityFactor。"""

    def __init__(self) -> None:
        self.session = None
        self.script = None
        self.app_pid: int | None = None
        self._lock = threading.RLock()

    def init_frida(self) -> None:
        from platforms.fanqie.device import attach_fanqie_session

        js_path = HERE / "oracle_sign.js"
        if not js_path.is_file():
            raise RuntimeError(f"missing sign oracle js: {js_path}")
        self.session, self.script, self.app_pid = attach_fanqie_session(
            js_path.read_text(encoding="utf-8")
        )

    def sign(self, url: str, headers: dict[str, str]) -> dict[str, str]:
        import concurrent.futures

        with self._lock:
            if not self.script:
                # attach 限时，避免 UI/API 永久挂起
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    fut = pool.submit(self.init_frida)
                    try:
                        fut.result(timeout=12.0)
                    except concurrent.futures.TimeoutError as exc:
                        self.close()
                        raise TimeoutError(
                            "Frida 连接番茄超时。请确认 sys_hlpd 与 com.dragon.read 在跑。"
                        ) from exc
            assert self.script is not None
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    fut = pool.submit(self.script.exports_sync.sign, url, headers)
                    return fut.result(timeout=10.0)
            except concurrent.futures.TimeoutError as exc:
                self.close()
                raise TimeoutError("番茄签名 RPC 超时，已断开 Frida 会话，请重试。") from exc
            except Exception:
                # 会话可能已僵死，下次重建
                self.close()
                raise

    def close(self) -> None:
        """仅 detach 本会话，不杀设备 agent（红果可继续用同一 agent）。"""
        with self._lock:
            if self.session:
                try:
                    self.session.detach()
                except Exception:
                    pass
                self.session = None
                self.script = None
                self.app_pid = None


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
    """从运行中的番茄 App 捕获新会话配置并重建签名连接。"""
    global _CFG

    get_oracle().close()
    grabber = REPO_ROOT / "tools" / "setup" / "grab_fanqie_config.py"
    if not grabber.is_file():
        raise RuntimeError(f"缺少番茄会话捕获脚本: {grabber}")
    result = subprocess.run(
        [sys.executable, str(grabber)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0 or not CFG_PATH.is_file():
        message = (result.stderr or result.stdout or "unknown error").strip()
        raise RuntimeError(f"番茄会话刷新失败: {message[-800:]}")
    with _CFG_LOCK:
        _CFG = json.loads(CFG_PATH.read_text(encoding="utf-8"))


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
            if attempt == 0 and getattr(e, "response", None) is not None:
                status = getattr(e.response, "status_code", 0)
                if status in {401, 403}:
                    try:
                        refresh_session()
                    except Exception:
                        pass
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
            # 兼容嵌套：cell / cell.book_data / cell.data
            src = cell if isinstance(cell, dict) else {}
            nested = src.get("book_data") or src.get("data") or src.get("book_info") or {}
            if not isinstance(nested, dict):
                nested = {}
            bid = (
                src.get("book_id")
                or src.get("search_result_id")
                or nested.get("book_id")
                or nested.get("search_result_id")
            )
            if not bid:
                continue
            bid = str(bid)
            if bid in seen:
                continue
            seen.add(bid)
            title = (
                src.get("book_name")
                or src.get("title")
                or nested.get("book_name")
                or nested.get("title")
                or nested.get("book_name_raw")
                or ""
            )
            # 部分响应 title 本身是数字 id，当作无标题
            if str(title).strip() == bid:
                title = ""
            author = src.get("author") or nested.get("author") or nested.get("author_name") or ""
            if isinstance(author, dict):
                author = author.get("name") or author.get("author_name") or ""
            cover = (
                src.get("cover")
                or src.get("thumb_url")
                or nested.get("cover")
                or nested.get("thumb_url")
                or nested.get("audio_thumb_uri")
                or ""
            )
            desc = (
                src.get("abstract")
                or src.get("desc")
                or nested.get("abstract")
                or nested.get("book_abstract")
                or nested.get("desc")
                or ""
            )
            results.append({
                "book_id": bid,
                "title": str(title or "") or bid,
                "author": str(author or ""),
                "cover": str(cover or ""),
                "desc": str(desc or ""),
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
            import logging

            logging.getLogger(__name__).warning("Directory fetch fail (%s): %s", path, e)
    return [], last


def fetch_full(book_id: str, item_id: str) -> dict[str, Any]:
    """拉取章节加密正文数据"""
    return api(
        "GET",
        "/reading/reader/full/v",
        extra_query={"item_id": item_id, "book_id": book_id, "novel_id": book_id},
    )
