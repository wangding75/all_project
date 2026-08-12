"""Full dump CryptManager.decrypt samples; pull to host; try offline AES."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tmp" / "fanqie_probe" / "crypt_dump"
OUT.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("ADB", r"D:\install\Netease\MuMu\nx_main\adb.exe")
from rd_device import resolve_device

os.environ["ADB_DEVICE"] = resolve_device()
os.environ.setdefault("FRIDA_HOST", "127.0.0.1:27042")
os.environ["PYTHONUNBUFFERED"] = "1"

ADB = os.environ["ADB"]
DEV = os.environ["ADB_DEVICE"]
FRIDA_HOST = os.environ["FRIDA_HOST"]
PKG = "com.dragon.read"
JS = Path(__file__).with_name("hook_fanqie_dump.js")
_AGENT_SRC = "/data/local/tmp/frida-server"
_AGENT_BIN = os.environ.get("AGENT_BIN", "/data/local/tmp/sys_hlpd")
_AGENT_NAME = Path(_AGENT_BIN).name

sys.path.insert(0, str(ROOT / "server" / ".venv" / "Lib" / "site-packages"))
import frida  # noqa: E402


def adb(*args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        [ADB, "-s", DEV, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
    )


def ensure_device() -> None:
    subprocess.run([ADB, "connect", DEV], capture_output=True, text=True)
    try:
        adb("root")
    except Exception:
        pass
    time.sleep(0.4)
    subprocess.run([ADB, "connect", DEV], capture_output=True, text=True)
    adb("forward", "tcp:27042", "tcp:27042")


def ensure_agent() -> None:
    """复用已有 agent；默认不 pkill（避免同机红果会话被杀）。设 FORCE_RESTART_AGENT=1 才强杀重建。"""
    ensure_device()
    force = os.environ.get("FORCE_RESTART_AGENT", "").strip() in {"1", "true", "yes"}
    if force:
        for name in ("frida-server", "frida", _AGENT_NAME, "fsd"):
            adb("shell", "pkill", "-9", name)
        time.sleep(0.4)
    pid = ""
    for name in (_AGENT_NAME, "frida-server", "sys_hlpd", "fsd"):
        pid = (adb("shell", "pidof", name).stdout or "").strip()
        if pid:
            print(f"[*] reuse agent {name} pid={pid}", flush=True)
            break
    if not pid:
        adb("shell", f"cp -f {_AGENT_SRC} {_AGENT_BIN} 2>/dev/null; chmod 755 {_AGENT_BIN} 2>/dev/null")
        subprocess.Popen(
            [ADB, "-s", DEV, "shell", _AGENT_BIN, "-D"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(1.5)
        pid = (adb("shell", "pidof", _AGENT_NAME).stdout or "").strip()
        print(f"[*] agent {_AGENT_NAME} pid={pid}", flush=True)
    adb("forward", "tcp:27042", "tcp:27042")
    if not pid and not (adb("shell", "pidof", "frida-server").stdout or "").strip():
        raise SystemExit("agent not running")
    frida.get_device_manager().add_remote_device(FRIDA_HOST).enumerate_processes()


def pull_dumps(host_dir: Path) -> int:
    host_dir.mkdir(parents=True, exist_ok=True)
    # pull whole dir
    r = adb("shell", "ls", "/data/local/tmp/fq_crypt")
    if "No such" in (r.stderr or "") or not (r.stdout or "").strip():
        return 0
    # adb pull
    dest = str(host_dir)
    subprocess.run(
        [ADB, "-s", DEV, "pull", "/data/local/tmp/fq_crypt/.", dest],
        capture_output=True,
        text=True,
    )
    n = len(list(host_dir.glob("*_meta.json")))
    return n


def main() -> int:
    duration = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 300
    ensure_device()
    app_pid = (adb("shell", "pidof", PKG).stdout or "").strip().split()
    if not app_pid:
        raise SystemExit("请先打开番茄小说 com.dragon.read")
    app_pid = app_pid[0]
    print(f"[*] {PKG} pid={app_pid}", flush=True)
    ensure_agent()
    # clear old dumps on device for clean run
    adb("shell", "rm", "-rf", "/data/local/tmp/fq_crypt")
    adb("shell", "mkdir", "-p", "/data/local/tmp/fq_crypt")

    log_path = OUT / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    dumps = 0
    ready = {"ok": False}

    def on_message(message, data):
        nonlocal dumps
        if message.get("type") == "error":
            print("[!] error", message.get("description") or message, flush=True)
            return
        payload = message.get("payload")
        if not isinstance(payload, dict):
            return
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        t = payload.get("t")
        if t == "log":
            print("[log]", payload.get("msg"), flush=True)
        elif t == "ready":
            ready["ok"] = True
            print("=" * 50, flush=True)
            print("[READY]", payload.get("msg"), flush=True)
            print(f"[READY] effective {duration}s — 请打开新章节", flush=True)
            print("=" * 50, flush=True)
        elif t == "methods":
            print(f"[methods] {payload.get('cls')}:", flush=True)
            for m in (payload.get("methods") or [])[:40]:
                print("  ", m[:180], flush=True)
        elif t == "fields":
            print(f"[fields] {payload.get('cls')}:", flush=True)
            for m in (payload.get("fields") or [])[:20]:
                print("  ", m[:180], flush=True)
        elif t == "dump":
            dumps += 1
            meta = payload.get("meta") or {}
            out = meta.get("out") or {}
            print(
                f"[DUMP #{dumps}] id={meta.get('id')} out_len={out.get('len')} "
                f"gzip={out.get('gzip')} html_len={out.get('html_len')} "
                f"head={out.get('html_head', '')[:60]!r}",
                flush=True,
            )
        elif t == "key":
            # 降噪：只打印 f/b
            if payload.get("method") in ("f", "b", "d"):
                print(f"[key] {payload.get('method')}={payload.get('ret')}", flush=True)

    print(f"[*] attach {app_pid}", flush=True)
    dev = frida.get_device_manager().add_remote_device(FRIDA_HOST)
    session = dev.attach(int(app_pid))
    script = session.create_script(JS.read_text(encoding="utf-8"))
    script.on("message", on_message)
    script.load()

    t0_wait = time.time()
    while not ready["ok"] and time.time() - t0_wait < 30:
        time.sleep(0.2)
    print(f"[*] EFFECTIVE WINDOW {duration}s", flush=True)
    t0 = time.time()
    last = 0
    try:
        while time.time() - t0 < duration:
            time.sleep(1)
            el = int(time.time() - t0)
            if el - last >= 30:
                last = el
                print(
                    f"[*] left={duration - el}s dumps={dumps}",
                    flush=True,
                )
                # 中途也 pull 一次
                if dumps > 0:
                    pull_dumps(OUT / "device")
    except KeyboardInterrupt:
        print("[*] interrupt", flush=True)
    finally:
        try:
            session.detach()
        except Exception:
            pass

    n = pull_dumps(OUT / "device")
    print(f"[*] pulled meta count~{n} dumps_msg={dumps}", flush=True)
    print(f"[*] host dir: {OUT / 'device'}", flush=True)
    print(f"[*] session log: {log_path}", flush=True)

    # 自动离线尝试
    try:
        from try_offline_fanqie_crypt import try_all  # type: ignore

        try_all(OUT / "device")
    except Exception as e:
        print(f"[*] offline try skipped/fail: {e}", flush=True)
        # inline minimal
        try_offline_inline(OUT / "device")
    return 0 if dumps else 2


def try_offline_inline(dump_dir: Path) -> None:
    """Try AES variants on dumped arg strings + out.bin."""
    import base64
    import gzip
    import hashlib

    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
    except ImportError:
        print("[!] pycryptodome missing", flush=True)
        return

    metas = sorted(dump_dir.glob("*_meta.json"))
    if not metas:
        print("[!] no meta on host", flush=True)
        return
    meta = json.loads(metas[0].read_text(encoding="utf-8"))
    args = meta.get("args") or []
    # find string paths
    cipher_b64 = None
    key_b64 = None
    version = None
    for a in args:
        if a.get("type") == "String" and a.get("path"):
            p = Path(a["path"])
            # device path — map to host
            name = Path(a["path"]).name
            hp = dump_dir / name
            if hp.exists():
                val = hp.read_text(encoding="utf-8", errors="replace").strip()
                if len(val) > 200:
                    cipher_b64 = val
                elif len(val) > 20:
                    key_b64 = val
        if a.get("type") == "String/other":
            v = a.get("value") or ""
            if v.isdigit():
                version = v
            elif 20 < len(v) < 200:
                key_b64 = v
    out_host = dump_dir / f"{meta.get('id')}_out.bin"
    if not out_host.exists():
        # try by id from filename
        outs = list(dump_dir.glob("*_out.bin"))
        out_host = outs[0] if outs else None
    print(f"[offline] cipher_len={len(cipher_b64 or '')} key={key_b64!r} ver={version}", flush=True)
    if not cipher_b64 or not key_b64:
        # read from arg txt files
        for f in dump_dir.glob("*_arg*.txt"):
            t = f.read_text(encoding="utf-8", errors="replace").strip()
            if len(t) > 200:
                cipher_b64 = t
            elif 20 < len(t) < 200:
                key_b64 = t
        for f in dump_dir.glob("*_meta.json"):
            m = json.loads(f.read_text(encoding="utf-8"))
            for a in m.get("args") or []:
                if a.get("type") == "String/other" and str(a.get("value", "")).isdigit():
                    version = a.get("value")
    if not cipher_b64 or not key_b64:
        print("[offline] missing cipher/key files", flush=True)
        return

    ct = base64.b64decode(cipher_b64)
    key = base64.b64decode(key_b64)
    print(f"[offline] ct={len(ct)} key={len(key)} key_hex={key.hex()}", flush=True)
    expected = None
    for f in dump_dir.glob("*_out.bin"):
        expected = f.read_bytes()
        print(f"[offline] expected out head={expected[:8].hex()} len={len(expected)}", flush=True)
        break

    candidates = []
    # AES-ECB
    if len(key) in (16, 24, 32):
        try:
            pt = AES.new(key, AES.MODE_ECB).decrypt(ct[: len(ct) - len(ct) % 16] or ct)
            candidates.append(("AES-ECB-raw", pt))
            try:
                candidates.append(("AES-ECB-unpad", unpad(pt, 16)))
            except Exception:
                pass
        except Exception as e:
            print("ECB fail", e)
    # AES-CBC iv=0 / iv=first16
    if len(key) in (16, 24, 32) and len(ct) > 16:
        for name, iv, data in [
            ("CBC-iv0", b"\x00" * 16, ct),
            ("CBC-iv-prefix", ct[:16], ct[16:]),
        ]:
            try:
                pt = AES.new(key, AES.MODE_CBC, iv).decrypt(data[: len(data) - len(data) % 16])
                candidates.append((name + "-raw", pt))
                try:
                    candidates.append((name + "-unpad", unpad(pt, 16)))
                except Exception:
                    pass
            except Exception:
                pass
    # AES-GCM: last 16 tag
    if len(key) in (16, 24, 32) and len(ct) > 28:
        for iv_len in (12, 16):
            try:
                iv, body, tag = ct[:iv_len], ct[iv_len:-16], ct[-16:]
                pt = AES.new(key, AES.MODE_GCM, nonce=iv).decrypt_and_verify(body, tag)
                candidates.append((f"GCM-iv{iv_len}", pt))
            except Exception:
                pass

    for name, pt in candidates:
        ok_gzip = pt[:2] == b"\x1f\x8b"
        match = expected is not None and pt == expected
        print(f"  try {name}: len={len(pt)} gzip={ok_gzip} exact={match} head={pt[:8].hex()}", flush=True)
        if ok_gzip or match:
            try:
                text = gzip.decompress(pt).decode("utf-8", "replace")
                print(f"  >>> SUCCESS {name} text_len={len(text)}", flush=True)
                print(text[:300], flush=True)
                (dump_dir / f"offline_{name}.html").write_text(text, encoding="utf-8")
            except Exception as e:
                print(f"  gunzip fail {e}", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
