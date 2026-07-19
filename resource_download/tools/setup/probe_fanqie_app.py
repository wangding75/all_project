"""Probe Fanqie (com.dragon.read): Frida sign + prefs config + book APIs."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse

import frida
import requests
import urllib3

urllib3.disable_warnings()

ADB = r"D:\install\Netease\MuMu\nx_main\adb.exe"
DEV = "127.0.0.1:16384"
FRIDA_HOST = "127.0.0.1:27042"
PKG = "com.dragon.read"
ORACLE_JS = Path(__file__).resolve().parents[2] / "vendor" / "hongguo" / "frida" / "oracle.js"
CFG_OUT = Path(__file__).resolve().parents[2] / "vendor" / "hongguo" / "config_fanqie.json"

DEVICE_KEYS = {
    "iid", "device_id", "ac", "channel", "aid", "app_name", "version_code",
    "version_name", "device_platform", "os", "ssmix", "device_type", "device_brand",
    "language", "os_api", "os_version", "manifest_version_code", "resolution", "dpi",
    "update_version_code", "host_abi", "dragon_device_type", "cdid", "klink_egdi",
}


def adb(*args: str) -> str:
    r = subprocess.run([ADB, "-s", DEV, *args], capture_output=True, text=True)
    return (r.stdout or "") + (r.stderr or "")


def pref(name: str, xml: str) -> str | None:
    m = re.search(rf'<string name="{re.escape(name)}">([^<]*)</string>', xml)
    return m.group(1) if m else None


def ensure() -> int:
    subprocess.run([ADB, "connect", DEV], capture_output=True)
    subprocess.run([ADB, "-s", DEV, "root"], capture_output=True)
    time.sleep(0.3)
    subprocess.run([ADB, "connect", DEV], capture_output=True)
    pid = adb("shell", "pidof", PKG).strip().split()
    if not pid:
        raise SystemExit("fanqie not running")
    if "frida-server" not in adb("shell", "ps", "-A"):
        adb("shell", "/data/local/tmp/frida-server -D &")
        time.sleep(2)
    adb("forward", "tcp:27042", "tcp:27042")
    return int(pid[0])


def build_cfg_from_prefs() -> dict:
    applog = adb("shell", "cat", f"/data/data/{PKG}/shared_prefs/applog_stats.xml")
    csrf = adb("shell", "cat", f"/data/data/{PKG}/shared_prefs/CsrfTokenManager_sp.xml")
    push = adb("shell", "cat", f"/data/data/{PKG}/shared_prefs/push_multi_process_config.xml")
    device_id = pref("device_id", applog) or ""
    install_id = pref("install_id", applog) or ""
    channel = pref("dr_channel", applog) or ""
    csrf_token = pref("csrf_token", csrf) or ""
    ssids = pref("ssids", push) or ""
    if ssids:
        m = re.search(r'"device_id"\s*:\s*"(\d+)"', ssids)
        if m and not device_id:
            device_id = m.group(1)
        m = re.search(r'"install_id"\s*:\s*"(\d+)"', ssids)
        if m and not install_id:
            install_id = m.group(1)
        m = re.search(r'"clientudid"\s*:\s*"([^"]+)"', ssids)
        cdid = m.group(1) if m else ""
    else:
        cdid = ""
    print("prefs device_id", device_id, "iid", install_id, "channel", channel)
    cfg = {
        "api_host": "api5-normal-sinfonlinea.fqnovel.com",
        "base_query": {
            "iid": install_id,
            "device_id": device_id,
            "aid": "1967",  # 番茄常见 aid，探测时会试 8662
            "app_name": "news_article_lite",  # 可能不对，后面用抓到的覆盖
            "version_code": "71932",
            "version_name": "7.1.9.32",
            "channel": channel or "novel_channel",
            "device_platform": "android",
            "device_type": "SM-S9210",
            "device_brand": "Samsung",
            "os_version": "15",
            "os_api": "35",
            "update_version_code": "71932",
            "cdid": cdid,
            "manifest_version_code": "71932",
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
                "com.dragon.read/71932 (Linux; U; Android 15; zh_CN; SM-S9210; "
                "Build/AP3A;tt-ok/3.12.13.20)"
            ),
            "sdk-version": "2",
            "passport-sdk-version": "5051452",
            "x-tt-store-region": "cn-sh",
            "x-tt-store-region-src": "uid",
        },
    }
    if csrf_token:
        cfg["session_headers"]["cookie"] = f"passport_csrf_token={csrf_token}; store-region=cn-sh"
    return cfg


def attach_oracle(pid: int):
    dev = frida.get_device_manager().add_remote_device(FRIDA_HOST)
    session = dev.attach(pid)
    script = session.create_script(ORACLE_JS.read_text(encoding="utf-8"))
    script.load()
    return session, script


def sign_headers(script, url: str, headers: dict) -> dict:
    signed = script.exports_sync.sign(url, headers)
    # normalize list-like values
    out = {}
    for k, v in signed.items():
        s = str(v) if v is not None else ""
        if s.startswith("[") and s.endswith("]"):
            s = s[1:-1]
        out[k] = s
    return out


def api_get(script, cfg: dict, path: str, extra_query: dict | None = None) -> dict:
    q = dict(cfg["base_query"])
    if extra_query:
        q.update(extra_query)
    url = f"https://{cfg['api_host']}{path}?{urlencode(q)}"
    headers = dict(cfg["session_headers"])
    headers.setdefault("content-type", "application/json; charset=utf-8")
    sec = sign_headers(script, url, headers)
    headers.update(sec)
    r = requests.get(url, headers=headers, timeout=30, verify=False)
    print("GET", path, "status", r.status_code, "len", len(r.content))
    try:
        return r.json()
    except Exception:
        print("body head", r.text[:300])
        return {"_raw": r.text[:500], "_status": r.status_code}


def try_grab(script, timeout_ms=25000) -> dict | None:
    try:
        return script.exports_sync.grab(timeout_ms)
    except Exception as e:
        print("grab fail", e)
        return None


def main() -> int:
    pid = ensure()
    print("pid", pid)
    cfg = build_cfg_from_prefs()
    session, script = attach_oracle(pid)
    print("oracle ok, smoke sign...")
    try:
        s = sign_headers(
            script,
            f"https://{cfg['api_host']}/reading/bookapi/search/tab/v/?aid=1967&query=test",
            {"user-agent": cfg["session_headers"]["user-agent"]},
        )
        print("sign keys", sorted(s.keys()))
    except Exception as e:
        print("sign fail", e)
        session.detach()
        return 2

    # poke UI then grab real query params
    adb("shell", "input", "swipe", "540", "600", "540", "1400", "300")
    print("grabbing traffic (swipe/search in app if needed)...")
    g = try_grab(script, 30000)
    if g and g.get("url"):
        print("grab url", g["url"][:180])
        q = dict(parse_qsl(urlparse(g["url"]).query))
        for k in DEVICE_KEYS:
            if q.get(k):
                cfg["base_query"][k] = q[k]
        headers = {str(k).lower(): str(v) for k, v in (g.get("headers") or {}).items()}
        for h in ("cookie", "x-tt-token", "user-agent", "passport-sdk-version", "sdk-version"):
            if headers.get(h):
                v = headers[h]
                if v.startswith("[") and v.endswith("]"):
                    v = v[1:-1]
                cfg["session_headers"][h] = v
        host = urlparse(g["url"]).hostname
        if host:
            cfg["api_host"] = host
        print("updated from grab, aid", cfg["base_query"].get("aid"), "app_name", cfg["base_query"].get("app_name"))
    else:
        print("no grab; try both aid 1967 and 8662 with prefs")

    CFG_OUT.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", CFG_OUT)

    # search probes
    for aid in (cfg["base_query"].get("aid"), "1967", "13", "8662"):
        if not aid:
            continue
        cfg["base_query"]["aid"] = str(aid)
        print("\n=== search aid=", aid)
        j = api_get(
            script,
            cfg,
            "/reading/bookapi/search/tab/v",
            {"query": "北派寻宝", "tab_name": "store", "offset": "0", "count": "10"},
        )
        code = j.get("code")
        tabs = j.get("search_tabs") or j.get("data") or []
        print("code", code, "keys", list(j.keys())[:12], "tabs_type", type(tabs).__name__)
        if isinstance(tabs, list) and tabs:
            print("tab0 keys", list(tabs[0].keys())[:15] if isinstance(tabs[0], dict) else tabs[0])
        if j.get("code") == 0 or (isinstance(tabs, list) and tabs):
            # try parse first book
            cells = []
            if isinstance(tabs, list):
                for t in tabs:
                    if isinstance(t, dict):
                        cells.extend(t.get("data") or t.get("cells") or [])
            print("cells", len(cells))
            if cells:
                c0 = cells[0] if isinstance(cells[0], dict) else {}
                print("cell sample", {k: c0.get(k) for k in list(c0)[:12]})
                book_id = str(c0.get("book_id") or c0.get("search_result_id") or "")
                if book_id:
                    print("\n=== directory book_id", book_id)
                    for path in (
                        "/reading/bookapi/directory/all_items/v",
                        "/reading/bookapi/directory/all_infos/v",
                        "/reading/bookapi/detail/v",
                    ):
                        dj = api_get(script, cfg, path, {"book_id": book_id})
                        print(path, "code", dj.get("code"), "keys", list(dj.keys())[:10])
                        # find item_id
                        text = json.dumps(dj, ensure_ascii=False)[:500]
                        print(" snippet", text[:200])
                    # try full chapter if we can find item_id
                    blob = json.dumps(dj if "dj" in dir() else {}, ensure_ascii=False)
            break

    session.detach()
    print("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
