"""从模拟器里红果 shared_prefs 拼一份最小 config.json。"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ADB = r"D:\install\Netease\MuMu\nx_main\adb.exe"
DEV = "127.0.0.1:16384"
OUT = Path(__file__).resolve().parents[2] / "vendor" / "hongguo" / "config.json"


def adb_pull_text(path: str) -> str:
    r = subprocess.run(
        [ADB, "-s", DEV, "shell", "cat", path],
        capture_output=True,
        text=True,
    )
    return r.stdout or ""


def pref(name: str, xml: str) -> str | None:
    m = re.search(rf'<string name="{re.escape(name)}">([^<]*)</string>', xml)
    return m.group(1) if m else None


def main() -> None:
    subprocess.run([ADB, "connect", DEV], capture_output=True)
    subprocess.run([ADB, "-s", DEV, "root"], capture_output=True)
    subprocess.run([ADB, "connect", DEV], capture_output=True)

    applog = adb_pull_text("/data/data/com.phoenix.read/shared_prefs/applog_stats.xml")
    push = adb_pull_text("/data/data/com.phoenix.read/shared_prefs/push_multi_process_config.xml")
    csrf = adb_pull_text("/data/data/com.phoenix.read/shared_prefs/CsrfTokenManager_sp.xml")

    device_id = pref("device_id", applog) or ""
    install_id = pref("install_id", applog) or ""
    channel = pref("dr_channel", applog) or "vivo_8662_64"
    device_token = pref("device_token", applog) or ""
    csrf_token = pref("csrf_token", csrf) or ""

    # ssids json in push prefs
    ssids = pref("ssids", push) or ""
    if ssids and not device_id:
        m = re.search(r'"device_id"\s*:\s*"(\d+)"', ssids)
        if m:
            device_id = m.group(1)
    if ssids and not install_id:
        m = re.search(r'"install_id"\s*:\s*"(\d+)"', ssids)
        if m:
            install_id = m.group(1)
    clientudid = ""
    if ssids:
        m = re.search(r'"clientudid"\s*:\s*"([^"]+)"', ssids)
        if m:
            clientudid = m.group(1)

    if not device_id or not install_id:
        raise SystemExit(f"missing ids device_id={device_id!r} iid={install_id!r}")

    cfg = {
        "api_host": "api5-normal-sinfonlinea.fqnovel.com",
        "base_query": {
            "iid": install_id,
            "device_id": device_id,
            "aid": "8662",
            "app_name": "novelread",
            "version_code": "70533",
            "version_name": "7.0.5.33",
            "channel": channel,
            "device_platform": "android",
            "device_type": "SM-S9210",
            "device_brand": "Samsung",
            "os_version": "15",
            "os_api": "35",
            "update_version_code": "70533",
            "cdid": clientudid or "",
            "klink_egdi": "",
            "manifest_version_code": "70533",
            "resolution": "1080*1920",
            "dpi": "480",
            "language": "zh",
            "os": "android",
            "ssmix": "a",
            "host_abi": "arm64-v8a",
            "ac": "wifi",
        },
        "session_headers": {
            "user-agent": (
                "com.phoenix.read/70533 (Linux; U; Android 15; zh_CN; SM-S9210; "
                "Build/AP3A.240905.015.A2;tt-ok/3.12.13.20)"
            ),
            "sdk-version": "2",
            "passport-sdk-version": "5051452",
            "x-tt-store-region": "cn-sh",
            "x-tt-store-region-src": "uid",
        },
        "_notes": "built from shared_prefs; guest session may lack x-tt-token",
    }
    if csrf_token:
        cfg["session_headers"]["cookie"] = f"passport_csrf_token={csrf_token}; store-region=cn-sh"
    if device_token:
        # some builds use device token as session surrogate; keep for debug
        cfg["session_headers"]["_device_token"] = device_token

    OUT.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT)
    print("device_id", device_id, "iid", install_id, "channel", channel)


if __name__ == "__main__":
    main()
