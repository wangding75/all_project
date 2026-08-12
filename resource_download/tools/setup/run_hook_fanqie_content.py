"""Attach Frida to 番茄 — timer starts AFTER hooks ready."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tmp" / "fanqie_probe" / "hook_hits"
OUT.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("ADB", r"D:\install\Netease\MuMu\nx_main\adb.exe")
from rd_device import resolve_device

os.environ["ADB_DEVICE"] = resolve_device()
os.environ.setdefault("FRIDA_HOST", "127.0.0.1:27042")
# 强制无缓冲，便于实时看日志
os.environ["PYTHONUNBUFFERED"] = "1"

ADB = os.environ["ADB"]
DEV = os.environ["ADB_DEVICE"]
FRIDA_HOST = os.environ["FRIDA_HOST"]
PKG_MAP = {
    "dragon": "com.dragon.read",
    "phoenix": "com.phoenix.read",
    "fanqie": "com.dragon.read",
    "hongguo": "com.phoenix.read",
}
JS = Path(__file__).with_name("hook_fanqie_content.js")

sys.path.insert(0, str(ROOT / "server" / ".venv" / "Lib" / "site-packages"))
import frida  # noqa: E402


def adb(*args: str, timeout: int = 40) -> subprocess.CompletedProcess:
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
    time.sleep(0.5)
    subprocess.run([ADB, "connect", DEV], capture_output=True, text=True)
    adb("forward", "tcp:27042", "tcp:27042")


# 源文件可保留原名（仅磁盘）；运行时进程名绝不能带 frida
_AGENT_SRC = "/data/local/tmp/frida-server"  # 仅作复制源，从不直接执行
# 默认伪装名：无 frida 字样（可用环境变量 AGENT_BIN 覆盖）
_AGENT_BIN = os.environ.get("AGENT_BIN", "/data/local/tmp/sys_hlpd")
_AGENT_NAME = Path(_AGENT_BIN).name
if "frida" in _AGENT_NAME.lower():
    raise SystemExit(f"AGENT_BIN 进程名不能含 frida: {_AGENT_NAME}")


def ensure_single_frida() -> None:
    """复制为无 frida 字样的文件名后启动；禁止以 frida-server 进程名运行。"""
    ensure_device()
    # 杀掉一切旧实例（含历史上的 frida-server / 别名）
    for name in ("frida-server", "frida", _AGENT_NAME, "fsd"):
        adb("shell", "pkill", "-9", name)
    time.sleep(0.5)
    # 确认源存在，复制为伪装名
    chk = adb("shell", "ls", "-l", _AGENT_SRC)
    if chk.returncode != 0 and "No such" in (chk.stderr or chk.stdout or ""):
        raise SystemExit(f"缺少源二进制 {_AGENT_SRC}，请先 push frida-server")
    r = adb(
        "shell",
        f"cp -f {_AGENT_SRC} {_AGENT_BIN} && chmod 755 {_AGENT_BIN} && ls -l {_AGENT_BIN}",
    )
    print(f"[*] agent bin (no frida in name): {(r.stdout or '').strip()}", flush=True)
    # 只执行伪装路径，绝不 exec 原 frida-server 路径
    subprocess.Popen(
        [ADB, "-s", DEV, "shell", _AGENT_BIN, "-D"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1.5)
    adb("forward", "tcp:27042", "tcp:27042")
    pid = (adb("shell", "pidof", _AGENT_NAME).stdout or "").strip()
    # 若仍出现名为 frida-server 的进程，立即杀掉（说明有人直启了源文件）
    leak = (adb("shell", "pidof", "frida-server").stdout or "").strip()
    if leak:
        print(f"[!] kill leaked frida-server pid={leak}", flush=True)
        adb("shell", "pkill", "-9", "frida-server")
        time.sleep(0.3)
        # 若伪装进程也被误杀则再起一次
        pid = (adb("shell", "pidof", _AGENT_NAME).stdout or "").strip()
        if not pid:
            subprocess.Popen(
                [ADB, "-s", DEV, "shell", _AGENT_BIN, "-D"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(1.2)
            pid = (adb("shell", "pidof", _AGENT_NAME).stdout or "").strip()
    print(f"[*] agent process name={_AGENT_NAME} pid={pid or '?'}", flush=True)
    # 进程列表自检：不得出现 frida 字样
    ps = adb("shell", "ps", "-A").stdout or ""
    bad = [ln for ln in ps.splitlines() if "frida" in ln.lower()]
    if bad:
        print("[!] still see frida in ps:", flush=True)
        for ln in bad[:5]:
            print("   ", ln, flush=True)
    else:
        print("[*] ps: no process name containing 'frida'", flush=True)
    try:
        frida.get_device_manager().add_remote_device(FRIDA_HOST).enumerate_processes()
        print("[*] agent remote port OK", flush=True)
    except Exception as e:
        raise SystemExit(f"agent port failed: {e}")
    if not pid:
        raise SystemExit(f"agent {_AGENT_NAME} not running")

def get_app_pid(pkg: str) -> str:
    ensure_device()
    pid = (adb("shell", "pidof", pkg).stdout or "").strip().split()
    if not pid:
        raise SystemExit(
            f"{pkg} 未运行。请先在模拟器手动打开番茄，稳定后再运行本脚本。"
        )
    print(f"[*] {pkg} pid={pid[0]}", flush=True)
    return pid[0]


def main() -> int:
    args = sys.argv[1:]
    # 默认 8 分钟有效窗口（从 ready 起算）
    duration = 480
    which = "dragon"
    for a in args:
        if a.isdigit():
            duration = int(a)
        elif a.lower() in PKG_MAP:
            which = a.lower()
    pkg = PKG_MAP[which]
    print(f"[*] target={pkg} effective_window={duration}s (from hooks READY)", flush=True)
    print("[*] setup: ensure frida (app must already be running)", flush=True)

    app_pid = get_app_pid(pkg)
    ensure_single_frida()
    # 再确认 app 还在（frida 启动不应杀它）
    app_pid2 = (adb("shell", "pidof", pkg).stdout or "").strip().split()
    if not app_pid2:
        raise SystemExit("App 在启动 frida 后消失了，请重新打开番茄后再试")
    app_pid = app_pid2[0]

    log_path = OUT / f"hits_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    plain_path = OUT / f"plain_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    print(f"[*] log -> {log_path}", flush=True)

    hits: list[dict] = []
    plains: list[str] = []
    ready = {"ok": False}

    def on_message(message, data):
        if message.get("type") == "error":
            print("[!] error", message.get("description") or message, flush=True)
            with log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"error": message}, ensure_ascii=False) + "\n")
            return
        payload = message.get("payload")
        if not isinstance(payload, dict):
            return
        t = payload.get("t")
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        if t == "log":
            print("[log]", payload.get("msg"), flush=True)
        elif t == "ready":
            ready["ok"] = True
            print("=" * 50, flush=True)
            print("[READY]", payload.get("msg"), flush=True)
            print(f"[READY] 有效计时 {duration}s 从现在开始", flush=True)
            print("[READY] 请慢慢打开一本书 → 点进一章 → 等正文出现", flush=True)
            print("=" * 50, flush=True)
        elif t == "classes":
            print(f"[classes] count={payload.get('count')}", flush=True)
            for n in (payload.get("names") or [])[:20]:
                print("  ", n, flush=True)
        elif t == "hit":
            hits.append(payload)
            tag = payload.get("tag")
            p = payload.get("p") or {}
            print(f"[HIT] {tag}", flush=True)
            for k, v in p.items():
                s = str(v)
                if len(s) > 200:
                    s = s[:200] + "..."
                print(f"   {k}: {s}", flush=True)
            text = p.get("text") or p.get("text_head") or p.get("ret") or ""
            if isinstance(text, str) and len(text) > 40:
                cn = sum(1 for c in text[:300] if "\u4e00" <= c <= "\u9fff")
                if cn >= 10:
                    plains.append(text)
                    with plain_path.open("a", encoding="utf-8") as f:
                        f.write(f"\n===== {tag} =====\n{text}\n")
                    print(f"   >>> PLAIN ({len(text)} chars)", flush=True)

    print(f"[*] attach {FRIDA_HOST} pid={app_pid}", flush=True)
    t_setup0 = time.time()
    try:
        dev = frida.get_device_manager().add_remote_device(FRIDA_HOST)
        session = dev.attach(int(app_pid))
    except Exception as e:
        print(f"[!] attach failed: {e}", flush=True)
        ensure_single_frida()
        time.sleep(1)
        dev = frida.get_device_manager().add_remote_device(FRIDA_HOST)
        session = dev.attach(int(app_pid))

    script = session.create_script(JS.read_text(encoding="utf-8"))
    script.on("message", on_message)
    try:
        script.load()
    except Exception as e:
        print(f"[!] load fail: {e}, retry...", flush=True)
        time.sleep(2)
        script = session.create_script(JS.read_text(encoding="utf-8"))
        script.on("message", on_message)
        script.load()

    print(f"[*] script loaded in {time.time() - t_setup0:.1f}s, wait for READY...", flush=True)

    # 等 ready，最多 30s；ready 后才开始正式计时
    t_wait = time.time()
    while not ready["ok"] and time.time() - t_wait < 30:
        time.sleep(0.2)
    if not ready["ok"]:
        print("[!] 未收到 ready 信号，仍按现在起算窗口", flush=True)
        ready["ok"] = True

    print(f"[*] EFFECTIVE WINDOW START: {duration}s", flush=True)
    t0 = time.time()
    last_report = 0
    try:
        while time.time() - t0 < duration:
            time.sleep(1)
            elapsed = int(time.time() - t0)
            if elapsed - last_report >= 30:
                last_report = elapsed
                left = duration - elapsed
                print(
                    f"[*] effective left={left}s hits={len(hits)} plains={len(plains)}",
                    flush=True,
                )
    except KeyboardInterrupt:
        print("[*] interrupted", flush=True)
    finally:
        try:
            session.detach()
        except Exception:
            pass

    print(f"[*] done hits={len(hits)} plains={len(plains)}", flush=True)
    print(f"[*] log: {log_path}", flush=True)
    if plains:
        print(f"[*] plain: {plain_path}", flush=True)
        return 0
    print("[*] 未抓到明文", flush=True)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
