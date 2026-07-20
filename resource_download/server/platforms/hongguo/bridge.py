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
def load_hongguo_api():
    """返回上游 hongguo 模块（H）。"""
    ensure_vendor()
    import hongguo as H  # type: ignore  # noqa: WPS433 — vendor path

    return H


@lru_cache(maxsize=1)
def load_offline_dl():
    """返回上游 offline_dl 模块。"""
    ensure_vendor()
    import offline_dl as ODL  # type: ignore  # noqa: WPS433

    return ODL


def vendor_ready() -> dict:
    """供 /health 或诊断用。"""
    root = vendor_root()
    install = _install_root()
    cfg = install / "data" / "config" / "hongguo_config.json"
    return {
        "vendor_path": str(root),
        "vendor_present": root.is_dir() and (root / "hongguo.py").is_file(),
        "config_present": cfg.is_file(),
        "unwrap_spade_present": (root / "frida" / "unwrap_spade.py").is_file(),
        "offline_dl_present": (root / "offline_dl.py").is_file(),
    }
