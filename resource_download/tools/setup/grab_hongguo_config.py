"""从运行中的红果 App 抓取一条真实请求，写入 data/config/hongguo_config.json。

用法:
  $env:ADB="adb"; $env:MUMU_INSTANCE_NAME="RD测试"
  python tools/setup/grab_hongguo_config.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import concurrent.futures
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

import frida

ADB = os.environ.get("ADB", "adb")
from rd_device import resolve_device

DEV = resolve_device()
FRIDA_HOST = os.environ.get("FRIDA_HOST", "127.0.0.1:27042")
PKG = os.environ.get("HONGGUO_PKG", "com.phoenix.read")

ROOT = Path(__file__).resolve().parents[2]
ORACLE_JS = ROOT / "vendor" / "hongguo" / "frida" / "oracle.js"
# 兼容本仓库 fanqie oracle 若红果 js 缺失
FALLBACK_JS = ROOT / "server" / "platforms" / "fanqie" / "oracle_sign.js"
OUT = ROOT / "data" / "config" / "hongguo_config.json"

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
    return ((r.stdout or "") + (r.stderr or "")).strip()


def get_device():
    for d in frida.get_device_manager().enumerate_devices():
        if d.id == DEV or (d.type == "usb" and DEV in d.id):
            return d
    subprocess.run([ADB, "-s", DEV, "forward", "tcp:27042", "tcp:27042"], capture_output=True)
    return frida.get_device_manager().add_remote_device(FRIDA_HOST)


def main() -> int:
    print(f"frida={frida.__version__} device={DEV} pkg={PKG}")
    subprocess.run([ADB, "connect", DEV], capture_output=True)
    # Do not unconditionally restart adbd: on MuMu this can tear down the
    # already-running root Frida bridge and leave a just-launched App with a
    # stale attach target. Root only when no pinned agent is present.
    existing_ps = adb("shell", "ps", "-A")
    if "sys_hlpd" not in existing_ps and "frida-server" not in existing_ps:
        subprocess.run([ADB, "-s", DEV, "root"], capture_output=True)
        time.sleep(0.4)
        subprocess.run([ADB, "connect", DEV], capture_output=True)

    pid_s = adb("shell", "pidof", PKG)
    if not pid_s:
        print("starting app...")
        adb("shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    # MuMu/Dragon apps can rotate the main PID while the launcher, WebView,
    # and plugin processes finish bootstrapping.  Poll instead of taking a
    # single snapshot at a fixed 10-second boundary.
    for _ in range(30):
        pid_s = adb("shell", "pidof", PKG).strip()
        if pid_s:
            break
        time.sleep(1)
    if not pid_s:
        print("FAIL: 红果 App 未运行")
        return 1
    ps = adb("shell", "ps", "-A")
    if "sys_hlpd" not in ps and "frida-server" not in ps:
        adb("shell", "nohup /data/local/tmp/sys_hlpd -D >/data/local/tmp/sys_hlpd.log 2>&1 &")
        time.sleep(2)
    adb("forward", "tcp:27042", "tcp:27042")

    js_path = ORACLE_JS if ORACLE_JS.is_file() else FALLBACK_JS
    if not js_path.is_file():
        print("FAIL: 无 oracle js", ORACLE_JS, FALLBACK_JS)
        return 1

    device = get_device()
    session = None
    pid = None
    # The launcher may replace the application process between pidof and
    # attach. Retry the current pidof set instead of pinning a stale process.
    for _ in range(20):
        for candidate in adb("shell", "pidof", PKG).split():
            try:
                pid = int(candidate)
                session = device.attach(pid)
                break
            except Exception:
                session = None
        if session is not None:
            break
        time.sleep(1)
    if session is None or pid is None:
        print("FAIL: unable to attach a live Hongguo PID")
        return 2
    print("attach", pid, "js", js_path.name)
    script = session.create_script(js_path.read_text(encoding="utf-8"))
    script.load()

    print("抓取网络签名请求中（触发 Hongguo 搜索）…")
    # The home feed may already be warm and produce only telemetry.  Trigger
    # the actual content search UI so oracle.js captures a /reading/ request.
    try:
        # Install the observer before generating UI traffic; otherwise the
        # first content request may complete before the hook is active.
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(script.exports_sync.grab, 50000)
            time.sleep(1)
            adb("shell", "input", "tap", "920", "125")
            time.sleep(1)
            adb("shell", "input", "text", "test")
            adb("shell", "input", "keyevent", "66")
            time.sleep(2)
            for _ in range(6):
                adb("shell", "input", "swipe", "540", "1500", "540", "400", "300")
                time.sleep(0.6)
                adb("shell", "input", "tap", "540", "800")
                time.sleep(0.5)
            grabbed = future.result(timeout=55)
    except Exception as e:
        print("grab FAIL:", e)
        session.detach()
        return 2

    url = grabbed.get("url") or ""
    headers = {
        str(k).lower(): (str(v).strip("[]") if v is not None else "")
        for k, v in (grabbed.get("headers") or {}).items()
    }
    for k, v in list(headers.items()):
        if v.startswith("[") and v.endswith("]"):
            headers[k] = v[1:-1]

    q = dict(parse_qsl(urlparse(url).query))
    base = {k: q[k] for k in DEVICE_KEYS if q.get(k)}
    sess = {h: headers[h] for h in SESSION_HEADERS if headers.get(h)}
    parsed = urlparse(url)
    host = parsed.hostname or "api5-normal-sinfonlinea.fqnovel.com"
    if "/reading/" not in parsed.path or host.startswith(("log", "mon")):
        print("FAIL: captured non-content endpoint", url)
        session.detach()
        return 3

    # 红果 aid 通常 8662；若抓到的是其它 aid 仍写入实际值
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cfg = {"api_host": host, "base_query": base, "session_headers": sess}
    OUT.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print("SUCCESS", OUT)
    print("device_id", base.get("device_id"), "iid", base.get("iid"), "aid", base.get("aid"))
    print("session keys", list(sess.keys()))
    session.detach()
    return 0 if base.get("device_id") else 4


if __name__ == "__main__":
    raise SystemExit(main())
