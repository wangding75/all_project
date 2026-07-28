"""番茄正文解密预言机：调用 **番茄 App** 内 native CryptManager.decrypt + gunzip。

依赖：
  - MuMu（或兼容模拟器）+ 已安装的 com.dragon.read
  - 设备上 Frida agent（可与红果共用同一 agent 端口，**分 pid attach**）
  - 本机 frida 与 agent 版本一致

**不依赖** com.phoenix.read / 红果签名能力。
**不会** pkill 设备上的 frida-server（避免打断同机红果会话）。

用法:
  from platforms.fanqie.crypt_oracle import FanqieCryptOracle
  o = FanqieCryptOracle()
  o.attach()
  html = o.decrypt_to_html(cipher_b64, key_b64, 1001)
"""

from __future__ import annotations

import gzip
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from platforms.fanqie.device import attach_fanqie_session, fanqie_pkg

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_JS = REPO_ROOT / "tools" / "setup" / "fanqie_crypt_oracle.js"


class FanqieCryptError(RuntimeError):
    pass


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
    def __init__(self, js_path: Path | None = None, pkg: str | None = None) -> None:
        self.js_path = js_path or DEFAULT_JS
        self.pkg = pkg or fanqie_pkg()
        self._session = None
        self._script = None
        self._app_pid: str | None = None

    @property
    def attached(self) -> bool:
        return self._script is not None

    def attach(self) -> None:
        if not self.js_path.is_file():
            raise FanqieCryptError(f"missing oracle js: {self.js_path}")
        # attach_fanqie_session 内部：复用 agent + 仅启动/attach 番茄进程
        try:
            self._session, self._script, app_pid = attach_fanqie_session(
                self.js_path.read_text(encoding="utf-8")
            )
            self._app_pid = str(app_pid)
        except RuntimeError as exc:
            raise FanqieCryptError(str(exc)) from exc

    def close(self) -> None:
        """仅 detach 本会话，不杀 agent。"""
        try:
            if self._session:
                self._session.detach()
        except Exception:
            pass
        self._session = None
        self._script = None
        self._app_pid = None

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
