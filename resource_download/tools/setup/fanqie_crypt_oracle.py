"""Fanqie content decrypt oracle via Frida RPC (native CryptManager.decrypt)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("ADB", r"D:\install\Netease\MuMu\nx_main\adb.exe")
os.environ.setdefault("ADB_DEVICE", "127.0.0.1:7555")
os.environ.setdefault("FRIDA_HOST", "127.0.0.1:27042")
os.environ.setdefault("AGENT_BIN", "/data/local/tmp/sys_hlpd")

ADB = os.environ["ADB"]
DEV = os.environ["ADB_DEVICE"]
FRIDA_HOST = os.environ["FRIDA_HOST"]
PKG = "com.dragon.read"
JS = Path(__file__).with_name("fanqie_crypt_oracle.js")
_AGENT_SRC = "/data/local/tmp/frida-server"
_AGENT_BIN = os.environ["AGENT_BIN"]
_AGENT_NAME = Path(_AGENT_BIN).name

sys.path.insert(0, str(ROOT / "server" / ".venv" / "Lib" / "site-packages"))
import frida  # noqa: E402

_session = None
_script = None


def adb(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [ADB, "-s", DEV, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=40,
    )


def ensure_agent() -> None:
    """复用已有 agent；禁止 pkill（同机红果签名会话需保留）。"""
    subprocess.run([ADB, "connect", DEV], capture_output=True)
    try:
        adb("root")
    except Exception:
        pass
    time.sleep(0.3)
    subprocess.run([ADB, "connect", DEV], capture_output=True)
    alive = False
    for name in (_AGENT_NAME, "frida-server", "sys_hlpd", "fsd"):
        if (adb("shell", "pidof", name).stdout or "").strip():
            alive = True
            break
    if not alive:
        adb("shell", f"cp -f {_AGENT_SRC} {_AGENT_BIN} 2>/dev/null; chmod 755 {_AGENT_BIN} 2>/dev/null")
        subprocess.Popen(
            [ADB, "-s", DEV, "shell", _AGENT_BIN, "-D"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(1.5)
        if not (adb("shell", "pidof", _AGENT_NAME).stdout or "").strip():
            subprocess.Popen(
                [ADB, "-s", DEV, "shell", _AGENT_SRC, "-D"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(1.5)
    adb("forward", "tcp:27042", "tcp:27042")


def attach(pkg: str = PKG):
    global _session, _script
    ensure_agent()
    pid = (adb("shell", "pidof", pkg).stdout or "").strip().split()
    if not pid:
        raise RuntimeError(f"{pkg} not running")
    dev = frida.get_device_manager().add_remote_device(FRIDA_HOST)
    _session = dev.attach(int(pid[0]))
    _script = _session.create_script(JS.read_text(encoding="utf-8"))
    _script.load()
    print(f"[*] oracle attached pid={pid[0]}", flush=True)
    return _script


def decrypt(cipher_b64: str, key_b64: str, key_version: int = 1001) -> dict:
    if _script is None:
        attach()
    assert _script is not None
    return _script.exports_sync.decrypt(cipher_b64, key_b64, int(key_version))


def main() -> int:
    """Test: probe full_resp + key from last hook."""
    key = "jvrM9i1ugTvR7z9HRo77iSeWIuGMvaH72hD+E3QB+N/rKkkmIzocQKxKE/qQJcNI"
    probe = ROOT / "tmp" / "fanqie_probe" / "full_resp.json"
    if not probe.exists():
        print("no probe file", flush=True)
        return 1
    data = json.loads(probe.read_text(encoding="utf-8"))["data"]
    content = data["content"]
    api_kv = data.get("key_version")
    print(f"[*] api key_version={api_kv} content_len={len(content)}", flush=True)
    attach()
    # try version 1001 (from DecryptKey) and api key_version
    for ver in (1001, int(api_kv) if api_kv else 1001, 0, 1):
        print(f"[*] try version={ver}", flush=True)
        r = decrypt(content, key, ver)
        print(
            f"  ok={r.get('ok')} out_len={r.get('out_len')} head={r.get('out_head_hex')} "
            f"gzip={r.get('gzip')} gunzip_err={r.get('gunzip_err')}",
            flush=True,
        )
        text = r.get("text") or ""
        if text:
            print(f"  TEXT len={len(text)}", flush=True)
            print(text[:400], flush=True)
            out = ROOT / "tmp" / "fanqie_probe" / f"oracle_v{ver}.html"
            out.write_text(text, encoding="utf-8")
            print(f"  wrote {out}", flush=True)
            return 0
        if r.get("error"):
            print(f"  err={r.get('error')}", flush=True)
    # also dump max key version
    mv = _script.exports_sync.max_key_version()
    print("[*] maxKeyVersion", mv, flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
