"""Loose grab: any NetworkParams.tryAddSecurityFactor call with fqnovel/device_id."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

import frida

ADB = r"D:\install\Netease\MuMu\nx_main\adb.exe"
DEV = os.environ.get("ADB_DEVICE", "127.0.0.1:7555")
FRIDA_HOST = "127.0.0.1:27042"
PKG = "com.phoenix.read"
OUT = Path(__file__).resolve().parents[2] / "data" / "config" / "hongguo_config.json"

JS = r"""
rpc.exports = {
  grab: function (timeoutMs) {
    return new Promise(function (resolve, reject) {
      Java.perform(function () {
        var NP = Java.use("com.bytedance.frameworks.baselib.network.http.NetworkParams");
        var ov = NP.tryAddSecurityFactor.overload("java.lang.String", "java.util.Map");
        var done = false;
        var seen = [];
        ov.implementation = function (url, h) {
          var ret = ov.call(this, url, h);
          try {
            var u = url.toString();
            seen.push(u.substring(0, 120));
            if (!done && (u.indexOf("fqnovel") >= 0 || u.indexOf("novel") >= 0 || u.indexOf("snssdk") >= 0)) {
              var o = {};
              var it = h.keySet().iterator();
              while (it.hasNext()) {
                var k = it.next();
                var v = h.get(k);
                o[k.toString()] = v ? v.toString() : null;
              }
              // also dump map after sign
              done = true;
              ov.implementation = null;
              resolve({url: u, headers: o, seen: seen});
            }
          } catch (e) {}
          return ret;
        };
        setTimeout(function () {
          if (!done) {
            ov.implementation = null;
            reject("timeout seen=" + JSON.stringify(seen.slice(0, 20)));
          }
        }, timeoutMs || 40000);
      });
    });
  }
};
"""

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
    if not adb("shell", "pidof", PKG).strip():
        adb("shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
        time.sleep(8)
    if "frida-server" not in adb("shell", "ps", "-A"):
        adb("shell", "/data/local/tmp/frida-server -D &")
        time.sleep(2)
    adb("forward", "tcp:27042", "tcp:27042")
    pid = int(adb("shell", "pidof", PKG).strip().split()[0])
    print("attach", pid)
    d = frida.get_device_manager().add_remote_device(FRIDA_HOST)
    s = d.attach(pid)
    sc = s.create_script(JS)
    sc.load()
    print("grabbing... poke UI")
    for _ in range(3):
        adb("shell", "input", "swipe", "540", "500", "540", "1400", "250")
        time.sleep(1)
        adb("shell", "input", "tap", "540", "1600")
        time.sleep(1)
    try:
        g = sc.exports_sync.grab(50000)
    except Exception as e:
        print("FAIL", e)
        s.detach()
        return 2
    print("got url", (g.get("url") or "")[:160])
    print("seen sample", (g.get("seen") or [])[:8])
    headers = {str(k).lower(): str(v) if v is not None else "" for k, v in (g.get("headers") or {}).items()}
    # strip list brackets if present
    for k, v in list(headers.items()):
        if v.startswith("[") and v.endswith("]"):
            headers[k] = v[1:-1]
    q = dict(parse_qsl(urlparse(g["url"]).query))
    base = {k: q[k] for k in DEVICE_KEYS if q.get(k)}
    sess = {h: headers[h] for h in SESSION_HEADERS if headers.get(h)}
    host = urlparse(g["url"]).hostname or "api5-normal-sinfonlinea.fqnovel.com"
    cfg = {"api_host": host, "base_query": base, "session_headers": sess}
    OUT.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT)
    print("device_id", base.get("device_id"), "keys", len(base), list(sess.keys()))
    s.detach()
    return 0


if __name__ == "__main__":
    sys.exit(main())
