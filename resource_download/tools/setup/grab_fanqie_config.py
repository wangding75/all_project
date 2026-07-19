"""Grab config for Fanqie: attach to com.dragon.read, grab NetworkParams.tryAddSecurityFactor."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

import frida

ADB = r"D:\install\Netease\MuMu\nx_main\adb.exe"
DEV = "127.0.0.1:16384"
FRIDA_HOST = "127.0.0.1:27042"
PKG = "com.dragon.read"

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


def main() -> int:
    subprocess.run([ADB, "connect", DEV], capture_output=True)
    subprocess.run([ADB, "-s", DEV, "root"], capture_output=True)
    time.sleep(0.3)
    subprocess.run([ADB, "connect", DEV], capture_output=True)
    
    # Check if app is running, else start it
    pids = adb("shell", "pidof", PKG).strip().split()
    if not pids:
        print(f"Starting {PKG}...")
        adb("shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
        time.sleep(8)
        pids = adb("shell", "pidof", PKG).strip().split()
    
    if not pids:
        print(f"FAIL: App {PKG} is not running.")
        return 1
        
    pid = int(pids[0])
    
    # Start Frida server if not running
    ps = adb("shell", "ps", "-A")
    if "sys_hlpd" not in ps and "frida-server" not in ps:
        print("Starting frida-server...")
        adb("shell", "/data/local/tmp/frida-server -D &")
        time.sleep(2)
        
    adb("forward", "tcp:27042", "tcp:27042")
    
    print(f"Attaching to PID {pid} ({PKG})...")
    d = frida.get_device_manager().add_remote_device(FRIDA_HOST)
    s = d.attach(pid)
    
    js_content = JS_FILE.read_text(encoding="utf-8")
    sc = s.create_script(js_content)
    sc.load()
    
    print("Grabbing... Please tap/swipe in Fanqie App to generate a request.")
    # Send a light swipe to trigger requests
    for _ in range(3):
        adb("shell", "input", "swipe", "540", "500", "540", "1400", "250")
        time.sleep(1)
        
    try:
        g = sc.exports_sync.grab(50000)
    except Exception as e:
        print("FAIL grab:", e)
        s.detach()
        return 2
        
    print("Got request URL:", (g.get("url") or "")[:120])
    headers = {str(k).lower(): str(v) if v is not None else "" for k, v in (g.get("headers") or {}).items()}
    # Clean brackets
    for k, v in list(headers.items()):
        if v.startswith("[") and v.endswith("]"):
            headers[k] = v[1:-1]
            
    q = dict(parse_qsl(urlparse(g["url"]).query))
    base = {k: q[k] for k in DEVICE_KEYS if q.get(k)}
    sess = {h: headers[h] for h in SESSION_HEADERS if headers.get(h)}
    host = urlparse(g["url"]).hostname or "api5-normal-sinfonlinea.fqnovel.com"
    
    cfg = {"api_host": host, "base_query": base, "session_headers": sess}
    OUT_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"SUCCESS: Wrote config to {OUT_FILE}")
    print("device_id:", base.get("device_id"), "iid:", base.get("iid"))
    print("session headers count:", len(sess))
    s.detach()
    return 0


if __name__ == "__main__":
    sys.exit(main())
