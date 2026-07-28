"""Grab config for Fanqie: attach to com.dragon.read, grab a real signed request.

用法:
  $env:ADB="adb"; $env:ADB_DEVICE="127.0.0.1:7555"
  python tools/setup/grab_fanqie_config.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

import frida

ADB = os.environ.get("ADB", "adb")
DEV = os.environ.get("ADB_DEVICE", "127.0.0.1:7555")
FRIDA_HOST = os.environ.get("FRIDA_HOST", "127.0.0.1:27042")
PKG = os.environ.get("FANQIE_PKG", "com.dragon.read")

ROOT = Path(__file__).resolve().parents[2]
JS_FILE = ROOT / "server" / "platforms" / "fanqie" / "oracle_sign.js"
OUT_FILE = ROOT / "data" / "config" / "fanqie_config.json"

DEVICE_KEYS = {
    "iid", "device_id", "ac", "channel", "aid", "app_name", "version_code",
    "version_name", "device_platform", "os", "ssmix", "device_type", "device_brand",
    "language", "os_api", "os_version", "manifest_version_code", "resolution", "dpi",
    "update_version_code", "host_abi", "dragon_device_type", "pv_player",
    "compliance_status", "need_personal_recommend", "player_so_load",
    "is_android_pad_screen", "rom_version", "cdid", "klink_egdi",
}
SESSION_HEADERS = (
    "cookie", "x-tt-token", "user-agent", "passport-sdk-version",
    "sdk-version", "x-tt-store-region", "x-tt-store-region-src",
)


def adb(*a: str) -> str:
    r = subprocess.run([ADB, "-s", DEV, *a], capture_output=True, text=True)
    return (r.stdout or "") + (r.stderr or "")


def get_frida_device():
    for d in frida.get_device_manager().enumerate_devices():
        if d.id == DEV or (d.type == "usb" and DEV in d.id):
            return d
    subprocess.run([ADB, "-s", DEV, "forward", "tcp:27042", "tcp:27042"], capture_output=True)
    return frida.get_device_manager().add_remote_device(FRIDA_HOST)


def main() -> int:
    print(f"frida={frida.__version__} adb={ADB} device={DEV}")
    subprocess.run([ADB, "connect", DEV], capture_output=True)
    subprocess.run([ADB, "-s", DEV, "root"], capture_output=True)
    time.sleep(0.3)
    subprocess.run([ADB, "connect", DEV], capture_output=True)

    pids = adb("shell", "pidof", PKG).strip().split()
    if not pids:
        print(f"Starting {PKG}...")
        adb("shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
        time.sleep(10)
        pids = adb("shell", "pidof", PKG).strip().split()

    if not pids:
        print(f"FAIL: App {PKG} is not running.")
        return 1

    pid = int(pids[0])

    ps = adb("shell", "ps", "-A")
    if "sys_hlpd" not in ps and "frida-server" not in ps:
        print("Starting agent sys_hlpd...")
        adb("shell", "nohup /data/local/tmp/sys_hlpd -D >/data/local/tmp/sys_hlpd.log 2>&1 &")
        time.sleep(2)

    adb("forward", "tcp:27042", "tcp:27042")

    print(f"Attaching to PID {pid} ({PKG})...")
    d = get_frida_device()
    s = d.attach(pid)

    js_content = JS_FILE.read_text(encoding="utf-8")
    sc = s.create_script(js_content)
    sc.load()

    # 先探测 Java
    probe = s.create_script(
        "rpc.exports={j:function(){return {t:typeof Java,a:(typeof Java!=='undefined'&&Java.available)};}};"
    )
    probe.load()
    jinfo = probe.exports_sync.j()
    print("Java bridge:", jinfo)
    if jinfo.get("t") != "object" or not jinfo.get("a"):
        print("FAIL: Java bridge unavailable. Use frida 16.7.19 + matching sys_hlpd.")
        s.detach()
        return 3

    print("Grabbing signed traffic (swipe to trigger network)...")
    for _ in range(5):
        adb("shell", "input", "swipe", "540", "500", "540", "1400", "250")
        time.sleep(0.8)
        adb("shell", "input", "tap", "540", "900")
        time.sleep(0.5)

    try:
        g = sc.exports_sync.grab(60000)
    except Exception as e:
        print("FAIL grab:", e)
        s.detach()
        return 2

    print("Got request URL:", (g.get("url") or "")[:160])
    headers = {
        str(k).lower(): str(v) if v is not None else ""
        for k, v in (g.get("headers") or {}).items()
    }
    for k, v in list(headers.items()):
        if v.startswith("[") and v.endswith("]"):
            headers[k] = v[1:-1]

    q = dict(parse_qsl(urlparse(g["url"]).query))
    base = {k: q[k] for k in DEVICE_KEYS if q.get(k)}
    sess = {h: headers[h] for h in SESSION_HEADERS if headers.get(h)}
    # 保留抓到的其它有用头
    for extra in ("x-ss-req-ticket", "x-argus", "x-gorgon", "x-khronos", "x-ladon"):
        if headers.get(extra) and extra not in sess:
            pass  # 签名头每次变，不写入长期 session
    host = urlparse(g["url"]).hostname or "api5-normal-sinfonlinea.fqnovel.com"

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    cfg = {"api_host": host, "base_query": base, "session_headers": sess}
    OUT_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"SUCCESS: Wrote config to {OUT_FILE}")
    print("device_id:", base.get("device_id"), "iid:", base.get("iid"))
    print("session headers:", list(sess.keys()))
    s.detach()
    return 0


if __name__ == "__main__":
    sys.exit(main())
