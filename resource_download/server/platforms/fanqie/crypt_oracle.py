"""番茄正文解密预言机：调用 App 内 native CryptManager.decrypt + gunzip。

依赖（与红果签名预言机类似）:
  - MuMu + 已登录/已打开的 com.dragon.read
  - /data/local/tmp 上的 agent 二进制（默认伪装名 sys_hlpd，源文件 frida-server）
  - 本机 frida 16.x 与 agent 版本一致

用法:
  from platforms.fanqie.crypt_oracle import FanqieCryptOracle
  o = FanqieCryptOracle()
  o.attach()
  html = o.decrypt_to_html(cipher_b64, key_b64, 1001)
"""

from __future__ import annotations

import gzip
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_JS = REPO_ROOT / "tools" / "setup" / "fanqie_crypt_oracle.js"

from app.config import get_settings

_settings = get_settings()
ADB = os.environ.get("ADB", _settings.adb_path)
DEV = os.environ.get("ADB_DEVICE", _settings.adb_device)
FRIDA_HOST = os.environ.get("FRIDA_HOST", _settings.frida_host)
PKG = os.environ.get("FANQIE_PKG", _settings.fanqie_pkg)
AGENT_SRC = os.environ.get("AGENT_SRC", "/data/local/tmp/sys_hlpd")
AGENT_BIN = os.environ.get("AGENT_BIN", "/data/local/tmp/sys_hlpd")
AGENT_NAME = Path(AGENT_BIN).name


class FanqieCryptError(RuntimeError):
    pass


def _adb(*args: str, timeout: int = 40) -> subprocess.CompletedProcess:
    return subprocess.run(
        [ADB, "-s", DEV, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def ensure_agent() -> str:
    """启动伪装名 agent，返回进程名。"""
    if "frida" in AGENT_NAME.lower():
        raise FanqieCryptError(f"AGENT_BIN name must not contain 'frida': {AGENT_NAME}")
    subprocess.run([ADB, "connect", DEV], capture_output=True)
    try:
        _adb("root")
    except Exception:
        pass
    time.sleep(0.3)
    subprocess.run([ADB, "connect", DEV], capture_output=True)
    for name in ("frida-server", "frida", AGENT_NAME, "fsd"):
        _adb("shell", "pkill", "-9", name)
    time.sleep(0.4)
    r = _adb("shell", f"cp -f {AGENT_SRC} {AGENT_BIN} && chmod 755 {AGENT_BIN}")
    if r.returncode != 0:
        raise FanqieCryptError(f"copy agent failed: {r.stderr or r.stdout}")
    subprocess.Popen(
        [ADB, "-s", DEV, "shell", AGENT_BIN, "-D"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1.5)
    _adb("forward", "tcp:27042", "tcp:27042")
    pid = (_adb("shell", "pidof", AGENT_NAME).stdout or "").strip()
    if not pid:
        raise FanqieCryptError(f"agent {AGENT_NAME} not running")
    return pid


def gunzip_bytes(data: bytes) -> str:
    if data[:2] != b"\x1f\x8b":
        raise FanqieCryptError(f"not gzip, head={data[:8].hex()}")
    return gzip.decompress(data).decode("utf-8", "replace")


@dataclass
class DecryptResult:
    ok: bool
    out_bytes: bytes | None = None
    text: str | None = None
    out_head_hex: str = ""
    error: str | None = None
    key_version: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "out_len": len(self.out_bytes) if self.out_bytes else 0,
            "out_head_hex": self.out_head_hex,
            "text_len": len(self.text) if self.text else 0,
            "error": self.error,
            "key_version": self.key_version,
        }


class FanqieCryptOracle:
    def __init__(self, js_path: Path | None = None, pkg: str = PKG) -> None:
        self.js_path = js_path or DEFAULT_JS
        self.pkg = pkg
        self._session = None
        self._script = None
        self._app_pid: str | None = None

    @property
    def attached(self) -> bool:
        return self._script is not None

    def attach(self) -> None:
        import frida  # type: ignore

        if not self.js_path.is_file():
            raise FanqieCryptError(f"missing oracle js: {self.js_path}")
        ensure_agent()
        app_pid = (_adb("shell", "pidof", self.pkg).stdout or "").strip().split()
        if not app_pid:
            raise FanqieCryptError(f"{self.pkg} not running — open 番茄 first")
        self._app_pid = app_pid[0]
        dev = frida.get_device_manager().add_remote_device(FRIDA_HOST)
        self._session = dev.attach(int(self._app_pid))
        self._script = self._session.create_script(self.js_path.read_text(encoding="utf-8"))
        self._script.load()

    def close(self) -> None:
        try:
            if self._session:
                self._session.detach()
        except Exception:
            pass
        self._session = None
        self._script = None

    def _exports(self):
        if self._script is None:
            self.attach()
        assert self._script is not None
        return self._script.exports_sync

    def max_key_version(self) -> int:
        r = self._exports().max_key_version()
        if not r.get("ok"):
            raise FanqieCryptError(r.get("error") or "max_key_version failed")
        return int(r["version"])

    def decrypt_raw(self, cipher_b64: str, key_b64: str, key_version: int = 1001) -> DecryptResult:
        import base64

        r = self._exports().decrypt(cipher_b64, key_b64, int(key_version))
        if not r.get("ok"):
            return DecryptResult(ok=False, error=r.get("error") or "decrypt failed", key_version=key_version)
        out_b64 = r.get("out_b64") or ""
        out = base64.b64decode(out_b64) if out_b64 else b""
        text = r.get("text")
        if text is None and out[:2] == b"\x1f\x8b":
            try:
                text = gunzip_bytes(out)
            except Exception as e:
                return DecryptResult(
                    ok=False,
                    out_bytes=out,
                    out_head_hex=r.get("out_head_hex") or out[:8].hex(),
                    error=f"gunzip: {e}",
                    key_version=key_version,
                )
        return DecryptResult(
            ok=True,
            out_bytes=out,
            text=text,
            out_head_hex=r.get("out_head_hex") or out[:8].hex(),
            key_version=key_version,
        )

    def decrypt_to_html(self, cipher_b64: str, key_b64: str, key_version: int = 1001) -> str:
        r = self.decrypt_raw(cipher_b64, key_b64, key_version)
        if not r.ok or not r.text:
            raise FanqieCryptError(r.error or "empty text")
        return r.text


# 本会话 dump 中观察到的密钥（设备/登录相关，可能过期；优先用 live DecryptKey）
DEFAULT_SESSION_KEY = (
    "jvrM9i1ugTvR7z9HRo77iSeWIuGMvaH72hD+E3QB+N/rKkkmIzocQKxKE/qQJcNI"
)
DEFAULT_KEY_VERSION = 1001
