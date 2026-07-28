"""番茄 App 设备侧运行时：仅依赖 com.dragon.read + 本机 Frida agent。

设计原则：
  - 签名与解密都 attach **番茄**进程，不依赖 com.phoenix.read（红果）。
  - 同一模拟器可并行跑红果 App 与番茄 App；**禁止** pkill 共用 frida-server/agent。
  - agent 已在跑则复用；仅在缺失时启动。
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from app.config import get_settings


def _settings():
    return get_settings()


def adb_bin() -> str:
    return os.environ.get("ADB", _settings().adb_path)


def adb_device() -> str:
    return os.environ.get("ADB_DEVICE", _settings().adb_device)


def frida_host() -> str:
    return os.environ.get("FRIDA_HOST", _settings().frida_host)


def fanqie_pkg() -> str:
    return os.environ.get("FANQIE_PKG", _settings().fanqie_pkg)


def agent_bin() -> str:
    """设备上 agent 路径（可伪装名）；默认 sys_hlpd 或 frida-server。"""
    return os.environ.get("AGENT_BIN", "/data/local/tmp/sys_hlpd")


def agent_src() -> str:
    return os.environ.get("AGENT_SRC", "/data/local/tmp/frida-server")


def adb(*args: str, timeout: int = 40) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [adb_bin(), "-s", adb_device(), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def connect() -> None:
    subprocess.run([adb_bin(), "connect", adb_device()], capture_output=True)


def pidof(name: str) -> str | None:
    out = (adb("shell", "pidof", name).stdout or "").strip()
    if not out:
        return None
    return out.split()[0]


def ensure_fanqie_running(*, launch_wait_sec: float = 8.0) -> int:
    """确保番茄小说进程存活，返回 pid。不涉及红果包名。"""
    from platforms.runtime import ensure_app_running

    st = ensure_app_running(fanqie_pkg(), launch_wait_sec=launch_wait_sec, try_start=True)
    if not st.get("running") or not st.get("pid"):
        raise RuntimeError(
            f"无法启动/获取番茄进程 {fanqie_pkg()}。请在模拟器中手动打开番茄小说。"
        )
    return int(st["pid"])


def _agent_running_names() -> list[str]:
    """返回当前可能在跑的 agent 进程名。"""
    names: list[str] = []
    agent_name = Path(agent_bin()).name
    for n in (agent_name, "frida-server", "sys_hlpd", "fsd"):
        if n and pidof(n):
            names.append(n)
    return names


def ensure_frida_agent(*, forward_port: int = 27042) -> str:
    """确保设备上有 Frida agent 在听，并做好端口转发。

    - **不** pkill 已有 agent（避免打掉红果签名会话）。
    - 已有 agent 则直接复用。
    - 缺失时优先启动 AGENT_BIN（可从 AGENT_SRC 复制），再回退 frida-server。
    """
    connect()
    try:
        adb("root", timeout=15)
    except Exception:
        pass
    time.sleep(0.2)
    connect()

    running = _agent_running_names()
    if not running:
        src = agent_src()
        bin_path = agent_bin()
        bin_name = Path(bin_path).name
        # 禁止用含 frida 的伪装名以外的强制规则：sys_hlpd 等均可
        # 尝试复制伪装二进制
        if bin_path != src:
            adb("shell", f"cp -f {src} {bin_path} 2>/dev/null; chmod 755 {bin_path} 2>/dev/null")
        started = False
        for candidate in (bin_path, src, "/data/local/tmp/frida-server"):
            cname = Path(candidate).name
            if pidof(cname):
                started = True
                break
            # 后台启动
            subprocess.Popen(
                [adb_bin(), "-s", adb_device(), "shell", candidate, "-D"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(1.5)
            if pidof(cname):
                started = True
                break
        if not started:
            # 最后一搏：shell 后台 &
            adb("shell", f"{bin_path} -D &")
            time.sleep(1.5)
            if not _agent_running_names():
                raise RuntimeError(
                    "Frida agent 未运行。请确认设备上存在 "
                    f"{agent_src()} 或 {agent_bin()}，且本机 frida 版本与 agent 一致。"
                )

    adb("forward", f"tcp:{forward_port}", f"tcp:{forward_port}")
    names = _agent_running_names()
    return names[0] if names else "frida-server"


def get_frida_device():
    """优先使用 adb USB 设备（id 常为 ADB_DEVICE）；失败再走 FRIDA_HOST 端口转发。"""
    import frida  # type: ignore

    target = adb_device()
    for d in frida.get_device_manager().enumerate_devices():
        if d.id == target or (d.type == "usb" and target in (d.id, d.name)):
            return d
    # 端口转发 + remote（旧路径）
    ensure_frida_agent()
    host = frida_host()
    return frida.get_device_manager().add_remote_device(host)


def probe_fanqie_runtime(*, try_start_agent: bool = False) -> dict:
    """探测番茄签名运行时（不 attach 业务脚本）。

    返回字段:
      ok: agent 与设备基本可用
      adb_device, adb_ok, agent_running, agent_names, fanqie_running, fanqie_pid
      agent_bin_on_device, message, hints
    """
    result: dict = {
        "ok": False,
        "adb_device": adb_device(),
        "adb_bin": adb_bin(),
        "adb_ok": False,
        "agent_running": False,
        "agent_names": [],
        "agent_bin": agent_bin(),
        "agent_bin_present": False,
        "fanqie_pkg": fanqie_pkg(),
        "fanqie_running": False,
        "fanqie_pid": None,
        "message": "",
        "hints": [],
    }
    try:
        connect()
        # adb 是否通：执行 echo
        r = adb("shell", "echo", "ok", timeout=8)
        result["adb_ok"] = (r.returncode == 0) and ("ok" in (r.stdout or ""))
        if not result["adb_ok"]:
            result["message"] = f"ADB 无法连接设备 {adb_device()}"
            result["hints"] = [
                f"检查模拟器是否启动，并 adb connect {adb_device()}",
                "或在 .env 设置 ADB_DEVICE=实际地址（adb devices 可见）",
            ]
            return result

        # agent 二进制是否在设备上
        ls = adb("shell", "ls", agent_bin(), timeout=8)
        result["agent_bin_present"] = ls.returncode == 0 and "No such" not in (ls.stderr or "")

        names = _agent_running_names()
        if not names and try_start_agent:
            try:
                ensure_frida_agent()
                names = _agent_running_names()
            except Exception as exc:
                result["hints"].append(f"尝试启动 agent 失败: {exc}")

        result["agent_names"] = names
        result["agent_running"] = bool(names)

        fpid = pidof(fanqie_pkg())
        result["fanqie_running"] = bool(fpid)
        result["fanqie_pid"] = fpid

        if not result["agent_running"]:
            result["message"] = "Frida agent 未运行（sys_hlpd / frida-server）"
            result["hints"] = [
                f"设备: {adb_device()}",
                f"push 并启动: adb -s {adb_device()} shell '{agent_bin()} -D &'",
                "或执行 tools/setup/push_frida.ps1",
            ]
            return result

        if not result["fanqie_running"]:
            result["message"] = "agent 已运行，但番茄 App 未打开"
            result["hints"] = [
                f"请启动 {fanqie_pkg()}（可进首页）",
                "书名搜索 / App 下载需要番茄进程",
            ]
            # agent 在即可做部分操作，但书名搜索仍可能失败
            result["ok"] = True  # 降级：agent 在算 ok，fanqie 仅提示
            result["degraded"] = True
            return result

        result["ok"] = True
        result["message"] = "番茄运行时就绪（agent + App）"
        return result
    except Exception as exc:
        result["message"] = f"探测异常: {exc}"
        result["hints"] = [f"检查 ADB_PATH / ADB_DEVICE（当前 {adb_device()}）"]
        return result


def attach_fanqie_session(js_source: str):
    """Attach 番茄进程并加载 Frida 脚本，返回 (session, script, app_pid)。

    仅 attach com.dragon.read，与红果进程无关。
    """
    # USB 路径下 frida-server 由 adb 自动转发；remote 路径需手动 ensure agent
    try:
        device = get_frida_device()
    except Exception:
        ensure_frida_agent()
        device = get_frida_device()

    # 若走 remote，仍确保 agent
    if getattr(device, "type", None) != "usb":
        ensure_frida_agent()

    app_pid = ensure_fanqie_running()
    session = device.attach(app_pid)

    # 预检 Java 桥：Magisk/LSPosed 环境下可能 attach 成功但 Java 全局不可用
    probe = session.create_script(
        r"""
rpc.exports = {
  check: function () {
    return {
      hasJava: typeof Java !== 'undefined',
      available: (typeof Java !== 'undefined' && Java.available)
    };
  }
};
"""
    )
    probe.load()
    try:
        st = probe.exports_sync.check()
    finally:
        try:
            probe.unload()
        except Exception:
            pass
    if not st.get("hasJava") or not st.get("available"):
        try:
            session.detach()
        except Exception:
            pass
        raise RuntimeError(
            "Frida 已 attach 番茄进程，但 Java 桥不可用（typeof Java === undefined）。"
            "这与红果无关。常见原因：Magisk/Zygisk/LSPosed 干扰、frida-server 与本机 frida 版本不匹配、"
            "或需重启模拟器后以 root 启动匹配版本的 frida-server。"
            f" 当前 pid={app_pid} device={getattr(device, 'id', device)}"
        )

    script = session.create_script(js_source)
    script.load()
    return session, script, app_pid
