"""用 frida oracle.grab 从运行中的红果 App 抓一条 fqnovel 请求，生成 config.json。"""
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
PKG = "com.phoenix.read"
ORACLE_JS = Path(__file__).resolve().parents[2] / "vendor" / "hongguo" / "frida" / "oracle.js"
OUT = Path(__file__).resolve().parents[2] / "data" / "config" / "hongguo_config.json"

DEVICE_KEYS = {
    "iid",
    "device_id",
    "ac",
    "channel",
    "aid",
    "app_name",
    "version_code",
    "version_name",
    "device_platform",
    "os",
    "ssmix",
    "device_type",
    "device_brand",
    "language",
    "os_api",
    "os_version",
    "manifest_version_code",
    "resolution",
    "dpi",
    "update_version_code",
    "host_abi",
    "dragon_device_type",
    "pv_player",
    "compliance_status",
    "need_personal_recommend",
    "player_so_load",
    "is_android_pad_screen",
    "rom_version",
    "cdid",
    "klink_egdi",
}
SESSION_HEADERS = (
    "cookie",
    "x-tt-token",
    "user-agent",
    "passport-sdk-version",
    "sdk-version",
    "x-tt-store-region",
    "x-tt-store-region-src",
)


def adb(*args: str) -> str:
    r = subprocess.run([ADB, "-s", DEV, *args], capture_output=True, text=True)
    return (r.stdout or "") + (r.stderr or "")


def ensure_env() -> int:
    subprocess.run([ADB, "connect", DEV], capture_output=True)
    subprocess.run([ADB, "-s", DEV, "root"], capture_output=True)
    time.sleep(0.5)
    subprocess.run([ADB, "connect", DEV], capture_output=True)
    pid = adb("shell", "pidof", PKG).strip().split()
    if not pid:
        adb("shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
        time.sleep(8)
        pid = adb("shell", "pidof", PKG).strip().split()
    if not pid:
        print("FAIL: app not running")
        return 0
    if "frida-server" not in adb("shell", "ps", "-A"):
        adb("shell", "/data/local/tmp/frida-server -D &")
        time.sleep(2)
    adb("forward", "tcp:27042", "tcp:27042")
    return int(pid[0])


def main() -> int:
    app_pid = ensure_env()
    if not app_pid:
        return 1
    # re-read pid
    pid = int(adb("shell", "pidof", PKG).strip().split()[0])
    print("attach", pid)
    device = frida.get_device_manager().add_remote_device(FRIDA_HOST)
    session = device.attach(pid)
    script = session.create_script(ORACLE_JS.read_text(encoding="utf-8"))
    script.load()
    print("oracle loaded; grab for up to 45s — 请在模拟器里点几下首页/搜索以产生网络请求")
    # poke app UI lightly
    adb("shell", "input", "tap", "500", "800")
    try:
        grabbed = script.exports_sync.grab(45000)
    except Exception as e:
        print("grab FAIL:", e)
        print("提示: 保持 App 前台并操作一次刷新/搜索后重试")
        session.detach()
        return 2

    url = grabbed.get("url") or ""
    headers = {k.lower(): v for k, v in (grabbed.get("headers") or {}).items()}
    q = dict(parse_qsl(urlparse(url).query))
    base_query = {k: q[k] for k in DEVICE_KEYS if q.get(k)}
    sess = {h: headers[h] for h in SESSION_HEADERS if headers.get(h)}
    # also keep original case keys from grab if missing
    for k, v in (grabbed.get("headers") or {}).items():
        lk = k.lower()
        if lk in SESSION_HEADERS and lk not in sess:
            sess[lk] = v

    host = urlparse(url).hostname or "api5-normal-sinfonlinea.fqnovel.com"
    cfg = {
        "api_host": host,
        "base_query": base_query,
        "session_headers": sess,
        "_source_url": url[:200],
    }
    OUT.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT)
    print("device_id", base_query.get("device_id"), "iid", base_query.get("iid"))
    print("base_query keys", len(base_query), sorted(base_query.keys())[:15], "...")
    print("session keys", list(sess.keys()))
    print("x-tt-token len", len(sess.get("x-tt-token") or ""))
    session.detach()
    return 0


if __name__ == "__main__":
    sys.exit(main())
