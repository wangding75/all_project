"""Attach to running com.phoenix.read and smoke-test oracle.js sign()."""
from __future__ import annotations

import subprocess
import sys
import time
import os
from pathlib import Path

import frida

ADB = os.environ.get("ADB", "adb")
from rd_device import resolve_device

DEV = resolve_device()
FRIDA_HOST = "127.0.0.1:27042"
PKG = "com.phoenix.read"
ORACLE_JS = Path(__file__).resolve().parents[2] / "vendor" / "hongguo" / "frida" / "oracle.js"


def sh(*args: str) -> str:
    r = subprocess.run([ADB, "-s", DEV, *args], capture_output=True, text=True)
    return (r.stdout or "") + (r.stderr or "")


def main() -> int:
    subprocess.run([ADB, "connect", DEV], capture_output=True)
    subprocess.run([ADB, "-s", DEV, "root"], capture_output=True)
    time.sleep(0.5)
    subprocess.run([ADB, "connect", DEV], capture_output=True)

    # ensure app
    pid_out = sh("shell", "pidof", PKG).strip().split()
    if not pid_out:
        print("launching app...")
        sh("shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
        time.sleep(8)
        pid_out = sh("shell", "pidof", PKG).strip().split()
    if not pid_out:
        print("FAIL: app not running")
        return 1
    app_pid = int(pid_out[0])
    print("app_pid", app_pid)

    # frida-server + forward
    if "frida-server" not in sh("shell", "ps", "-A"):
        sh("shell", "/data/local/tmp/frida-server -D &")
        time.sleep(2)
    sh("forward", "tcp:27042", "tcp:27042")

    device = frida.get_device_manager().add_remote_device(FRIDA_HOST)
    # re-read pid (may change)
    pid_out = sh("shell", "pidof", PKG).strip().split()
    app_pid = int(pid_out[0])
    print("attach", app_pid)
    session = device.attach(app_pid)
    script = session.create_script(ORACLE_JS.read_text(encoding="utf-8"))
    script.load()
    print("oracle loaded")
    try:
        result = script.exports_sync.sign(
            "https://api5-normal-sinfonlinea.fqnovel.com/reading/bookapi/search/tab/v/?aid=8662",
            {"user-agent": "com.phoenix.read/70533"},
        )
        print("sign ok, keys:", sorted(result.keys()) if isinstance(result, dict) else result)
        if isinstance(result, dict):
            for k in list(result.keys())[:12]:
                v = str(result[k])
                print(f"  {k}: {v[:80]}{'...' if len(v) > 80 else ''}")
    except Exception as e:
        print("sign FAIL:", type(e).__name__, e)
        session.detach()
        return 2
    session.detach()
    print("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
