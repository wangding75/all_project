"""Grab config for Fanqie: attach to com.dragon.read, grab a real signed request.

用法:
  $env:ADB="adb"; $env:MUMU_INSTANCE_NAME="RD测试"
  python tools/setup/grab_fanqie_config.py
"""
from __future__ import annotations

import json
import os
import html
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

import frida

ADB = os.environ.get("ADB", "adb")
from rd_device import resolve_device

DEV = resolve_device()
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


def pref(name: str, xml: str) -> str | None:
    match = re.search(rf'<string name="{re.escape(name)}">([^<]*)</string>', xml)
    return html.unescape(match.group(1)) if match else None


def build_cfg_from_prefs() -> dict:
    """Build guest-device metadata from the installed RD Fanqie App.

    This is a recovery path for a clean-state where no captured request file
    remains.  It reads App-owned device/session metadata and still signs every
    request through the live Java bridge; it never invents a signed session or
    accepts a user login credential.
    """
    applog = adb("shell", "cat", f"/data/data/{PKG}/shared_prefs/applog_stats.xml")
    csrf = adb("shell", "cat", f"/data/data/{PKG}/shared_prefs/CsrfTokenManager_sp.xml")
    push = adb("shell", "cat", f"/data/data/{PKG}/shared_prefs/push_multi_process_config.xml")
    device_id = pref("device_id", applog) or ""
    install_id = pref("install_id", applog) or ""
    channel = pref("dr_channel", applog) or ""
    csrf_token = pref("csrf_token", csrf) or ""
    ssids = pref("ssids", push) or ""
    cdid = ""
    if ssids:
        device_id = device_id or (re.search(r'"device_id"\s*:\s*"(\d+)"', ssids) or ["", ""])[1]
        install_id = install_id or (re.search(r'"install_id"\s*:\s*"(\d+)"', ssids) or ["", ""])[1]
        cdid_match = re.search(r'"clientudid"\s*:\s*"([^"]+)"', ssids)
        cdid = cdid_match.group(1) if cdid_match else ""

    package_info = adb("shell", "dumpsys", "package", PKG)
    version_code = (re.search(r"versionCode=(\d+)", package_info) or ["", "71932"])[1]
    version_name = (re.search(r"versionName=([^\s]+)", package_info) or ["", "7.1.9.32"])[1]
    if not device_id or not install_id:
        raise RuntimeError("Fanqie App prefs 缺少 device_id/iid")

    cfg = {
        "api_host": "api5-normal-sinfonlinea.fqnovel.com",
        "base_query": {
            "iid": install_id,
            "device_id": device_id,
            "aid": "1967",
            "app_name": "novelread",
            "version_code": version_code,
            "version_name": version_name,
            "channel": channel or "novel_channel",
            "device_platform": "android",
            "device_type": "SM-S9210",
            "device_brand": "Samsung",
            "os_version": "15",
            "os_api": "35",
            "update_version_code": version_code,
            "cdid": cdid,
            "manifest_version_code": version_code,
            "resolution": "1080*1920",
            "dpi": "480",
            "language": "zh",
            "os": "android",
            "ssmix": "a",
            "host_abi": "x86_64",
            "ac": "wifi",
        },
        "session_headers": {
            "user-agent": f"com.dragon.read/{version_code} (Linux; U; Android 15; zh_CN; SM-S9210; Build/AP3A;tt-ok/3.12.13.20)",
            "sdk-version": "2",
            "passport-sdk-version": "5051452",
            "x-tt-store-region": "cn-sh",
            "x-tt-store-region-src": "uid",
        },
        "source": "fanqie_app_prefs",
    }
    if csrf_token:
        cfg["session_headers"]["cookie"] = f"passport_csrf_token={csrf_token}; store-region=cn-sh"
    return cfg


def adb(*a: str) -> str:
    r = subprocess.run(
        [ADB, "-s", DEV, *a],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
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
    # Do not restart adbd when the formal RD bootstrap already has a live
    # root agent: adb root can tear down the just-started bridge on a MuMu
    # restart.  Standalone use still obtains root when the agent is absent.
    existing_ps = adb("shell", "ps", "-A")
    if "sys_hlpd" not in existing_ps and "frida-server" not in existing_ps:
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
        g = sc.exports_sync.grab(20000)
    except Exception as e:
        print("WARN grab:", e)
        # A freshly installed guest App can have no natural request in the
        # observation window.  Recover from its own prefs while retaining the
        # live Java bridge as the signing authority.
        try:
            cfg = build_cfg_from_prefs()
        except Exception as prefs_exc:
            print("FAIL App prefs recovery:", prefs_exc)
            s.detach()
            return 2
        OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUT_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"SUCCESS: Recovered config from Fanqie App prefs to {OUT_FILE}")
        print("session headers:", list(cfg["session_headers"].keys()))
        s.detach()
        return 0

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
