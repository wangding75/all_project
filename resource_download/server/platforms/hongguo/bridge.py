"""把 vendor/hongguo 挂到 sys.path，供本仓库 adapter 复用。

不复制算法代码：运行时 import 上游模块。
需要本机已放置:
  - vendor/hongguo/ （git clone https://github.com/zhangbaio/hongguo.git）
  - vendor/hongguo/config.json（设备/会话，见上游 extract_config / config.example.json）
  - 可用的签名后端（Frida oracle 或 SIGN_SERVER / unidbg，见上游 README）
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Callable, TypeVar


T = TypeVar("T")


def _install_root() -> Path:
    """与 app.config.REPO_ROOT 一致：exe 旁 / 环境变量 / 源码仓库根。"""
    try:
        from app.config import REPO_ROOT

        return REPO_ROOT
    except Exception:  # noqa: BLE001
        return Path(__file__).resolve().parents[3]


class HongguoVendorError(RuntimeError):
    pass


def vendor_root() -> Path:
    return _install_root() / "vendor" / "hongguo"


def ensure_vendor() -> Path:
    root = vendor_root()
    if not root.is_dir():
        raise HongguoVendorError(
            f"missing vendor at {root}. Run: "
            "git clone --depth 1 https://github.com/zhangbaio/hongguo.git vendor/hongguo"
        )
    if not (root / "hongguo.py").is_file():
        raise HongguoVendorError(f"incomplete vendor: no hongguo.py under {root}")
    # offline_dl 依赖 frida/ 下的 offline_decrypt
    frida_dir = root / "frida"
    for p in (str(root), str(frida_dir)):
        if p not in sys.path:
            sys.path.insert(0, p)
    return root


@lru_cache(maxsize=1)
def load_offline_dl():
    """返回上游 offline_dl 模块。"""
    ensure_vendor()
    ensure_config()
    import offline_dl as ODL  # type: ignore  # noqa: WPS433

    return ODL


def config_path() -> Path:
    """与 vendor/hongguo/hongguo.py 中 CFG_PATH 一致。"""
    return _install_root() / "data" / "config" / "hongguo_config.json"


def ensure_config() -> Path:
    """红果 API 导入前必须有会话配置，否则给出明确中文错误。"""
    path = config_path()
    if path.is_file():
        return path
    # 兼容上游默认：vendor/hongguo/config.json
    alt = vendor_root() / "config.json"
    if alt.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(alt.read_text(encoding="utf-8"), encoding="utf-8")
        return path
    raise HongguoVendorError(
        "缺少红果会话配置 data/config/hongguo_config.json。"
        "请先准备设备会话（推荐）: "
        "python tools/setup/grab_hongguo_config.py"
        "（需模拟器红果 App + sys_hlpd），"
        "或复制 vendor/hongguo/config.example.json 为 data/config/hongguo_config.json 并填入真实值。"
    )


@lru_cache(maxsize=1)
def load_hongguo_api():
    """返回上游 hongguo 模块（H）。"""
    ensure_vendor()
    ensure_config()
    import hongguo as H  # type: ignore  # noqa: WPS433 — vendor path

    return H


def _is_dead_frida_session(exc: BaseException) -> bool:
    if isinstance(exc, IndexError):
        # The vendor oracle indexes pidof(...).split()[0]; an empty result means
        # the App exited between the runtime probe and Frida attach.
        return True
    if type(exc).__name__ in {
        "InvalidOperationError",
        "PermissionDeniedError",
        "ProcessNotFoundError",
        "RPCException",
        "TransportError",
    }:
        return True
    message = str(exc).lower()
    return any(
        marker in message
        for marker in (
            "script has been destroyed",
            "session is detached",
            "connection is closed",
            "transport error",
            "invalid operation",
            "timed out trying to sync up with agent",
            "unable to communicate with remote frida-server",
            "unable to access process",
            "no such process",
            "unable to write to process memory",
            "process is not responding",
        )
    )


def _reset_local_oracle() -> None:
    """Discard the vendor's cached Frida session after the app process restarts."""
    H = load_hongguo_api()
    lock = getattr(H, "_oracle_lock", None)
    if lock is None:
        setattr(H, "_oracle", None)
        return
    with lock:
        old = getattr(H, "_oracle", None)
        setattr(H, "_oracle", None)
        session = getattr(old, "session", None)
        if session is not None:
            try:
                session.detach()
            except Exception:  # noqa: BLE001 - the old session is already unusable
                pass


def _ensure_hongguo_runtime() -> None:
    from app.config import get_settings
    from platforms.device_discovery import resolve_rd_test_device
    from platforms.runtime import ensure_app_running, probe_shared_agent
    from platforms.hongguo.frida_compat import ensure_compatible

    settings = get_settings()
    device = resolve_rd_test_device(force=True, settings=settings)
    import os

    # The upstream vendor reads ADB (not ADB_PATH). Keep both names in sync so
    # a package deployment with MuMu's adb outside PATH cannot fail at import.
    os.environ["ADB"] = str(settings.adb_path or os.environ.get("ADB") or "adb")
    os.environ["ADB_DEVICE"] = device.serial
    ensure_compatible()
    agent = probe_shared_agent(try_start=True)
    if not agent.get("agent_running"):
        raise RuntimeError(agent.get("message") or "Frida agent unavailable")
    app = ensure_app_running(settings.hongguo_pkg, try_start=True)
    if not app.get("running"):
        raise RuntimeError(app.get("message") or "Hongguo App unavailable")
    H = load_hongguo_api()
    if getattr(H, "DEV", device.serial) != device.serial:
        _reset_local_oracle()
        if hasattr(H, "set_adb_device"):
            H.set_adb_device(device.serial)
        else:
            H.DEV = device.serial


def call_with_session_recovery(operation: Callable[[], T]) -> T:
    """Retry one signed vendor operation after rebuilding a stale Frida session."""
    _ensure_hongguo_runtime()
    try:
        return operation()
    except Exception as exc:
        if not _is_dead_frida_session(exc):
            raise
        _reset_local_oracle()
        _ensure_hongguo_runtime()
        return operation()


def vendor_ready() -> dict:
    """供 /health 或诊断用。"""
    root = vendor_root()
    cfg = config_path()
    return {
        "vendor_present": root.is_dir() and (root / "hongguo.py").is_file(),
        "config_present": cfg.is_file(),
        "unwrap_spade_present": (root / "frida" / "unwrap_spade.py").is_file(),
        "offline_dl_present": (root / "offline_dl.py").is_file(),
        "ok": root.is_dir() and (root / "hongguo.py").is_file() and cfg.is_file(),
    }
