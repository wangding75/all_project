"""多平台设备运行时：共享 Frida agent + 各平台 App 探测/自启。

服务端启动与 /health 使用。客户端不调用本模块。
"""

from __future__ import annotations

import logging
from typing import Any

from app.config import get_settings
from platforms.fanqie import device as dev

logger = logging.getLogger(__name__)

# 各 App 常用启动组件（失败再 monkey）
_APP_LAUNCH: dict[str, list[str]] = {
    "com.dragon.read": [
        "com.dragon.read/.pages.main.MainFragmentActivity",
        "com.dragon.read/.pages.splash.SplashActivity",
    ],
    "com.phoenix.read": [
        "com.phoenix.read/.pages.splash.SplashActivity",
        "com.phoenix.read/.pages.main.MainFragmentActivity",
    ],
}


def hongguo_pkg() -> str:
    import os

    return os.environ.get("HONGGUO_PKG", get_settings().hongguo_pkg)


def ensure_app_running(
    pkg: str,
    *,
    launch_wait_sec: float = 8.0,
    try_start: bool = True,
) -> dict[str, Any]:
    """确保指定包名进程在跑；try_start 时自动 am start / monkey。"""
    import time

    out: dict[str, Any] = {
        "pkg": pkg,
        "running": False,
        "pid": None,
        "started": False,
        "message": "",
    }
    dev.connect()
    pid = dev.pidof(pkg)
    if pid:
        out["running"] = True
        out["pid"] = pid
        out["message"] = "already running"
        return out

    if not try_start:
        out["message"] = f"{pkg} 未运行"
        return out

    # 尝试声明的 Activity
    for component in _APP_LAUNCH.get(pkg, []):
        dev.adb("shell", "am", "start", "-n", component)
        time.sleep(min(3.0, launch_wait_sec))
        pid = dev.pidof(pkg)
        if pid:
            out["running"] = True
            out["pid"] = pid
            out["started"] = True
            out["message"] = f"started via {component}"
            return out

    # monkey 启动器
    dev.adb(
        "shell",
        "monkey",
        "-p",
        pkg,
        "-c",
        "android.intent.category.LAUNCHER",
        "1",
    )
    time.sleep(launch_wait_sec)
    pid = dev.pidof(pkg)
    if pid:
        out["running"] = True
        out["pid"] = pid
        out["started"] = True
        out["message"] = "started via monkey"
        return out

    out["message"] = f"无法启动 {pkg}，请手动在模拟器打开"
    return out


def probe_shared_agent(*, try_start: bool = False) -> dict[str, Any]:
    """共享 Frida agent 状态。"""
    result: dict[str, Any] = {
        "ok": False,
        "adb_device": dev.adb_device(),
        "adb_ok": False,
        "agent_running": False,
        "agent_names": [],
        "agent_bin": dev.agent_bin(),
        "agent_bin_present": False,
        "message": "",
        "hints": [],
    }
    try:
        dev.connect()
        r = dev.adb("shell", "echo", "ok", timeout=8)
        result["adb_ok"] = r.returncode == 0 and "ok" in (r.stdout or "")
        if not result["adb_ok"]:
            result["message"] = f"ADB 无法连接 {dev.adb_device()}"
            result["hints"] = [
                f"adb connect {dev.adb_device()}",
                "检查 .env 中 ADB_DEVICE 是否与 adb devices 一致",
            ]
            return result

        ls = dev.adb("shell", "ls", dev.agent_bin(), timeout=8)
        result["agent_bin_present"] = ls.returncode == 0 and "No such" not in (ls.stderr or "")

        names = dev._agent_running_names()
        if not names and try_start:
            try:
                dev.ensure_frida_agent()
                names = dev._agent_running_names()
            except Exception as exc:
                result["hints"].append(f"启动 agent 失败: {exc}")

        result["agent_names"] = names
        result["agent_running"] = bool(names)
        if not result["agent_running"]:
            result["message"] = "Frida agent 未运行（sys_hlpd）"
            result["hints"] = [
                f"adb -s {dev.adb_device()} shell '{dev.agent_bin()} -D &'",
                "或 tools/setup/push_frida.ps1",
            ]
            return result

        result["ok"] = True
        result["message"] = "agent 就绪"
        return result
    except Exception as exc:
        result["message"] = str(exc)
        return result


def probe_platform_apps(*, try_start_apps: bool = False) -> dict[str, Any]:
    """探测并可选启动番茄 + 红果 App。"""
    settings = get_settings()
    apps = {
        "fanqie": settings.fanqie_pkg,
        "hongguo": settings.hongguo_pkg,
    }
    out: dict[str, Any] = {"ok": True, "apps": {}}
    for name, pkg in apps.items():
        st = ensure_app_running(pkg, try_start=try_start_apps)
        out["apps"][name] = st
        if not st.get("running"):
            out["ok"] = False
    return out


def probe_all_runtimes(
    *,
    try_start_agent: bool = False,
    try_start_apps: bool = False,
) -> dict[str, Any]:
    """完整设备运行时：ADB + 共享 agent + 各平台 App。"""
    agent = probe_shared_agent(try_start=try_start_agent)
    apps = probe_platform_apps(try_start_apps=try_start_apps and agent.get("adb_ok", False))

    fanqie = apps["apps"].get("fanqie") or {}
    hongguo = apps["apps"].get("hongguo") or {}

    # 兼容旧 fanqie_runtime 字段形状
    fanqie_runtime = {
        **agent,
        "fanqie_pkg": fanqie.get("pkg"),
        "fanqie_running": fanqie.get("running"),
        "fanqie_pid": fanqie.get("pid"),
        "fanqie_started": fanqie.get("started"),
        "ok": bool(agent.get("agent_running") and fanqie.get("running")),
        "degraded": bool(agent.get("agent_running") and not fanqie.get("running")),
        "message": (
            "番茄运行时就绪"
            if agent.get("agent_running") and fanqie.get("running")
            else (
                agent.get("message")
                if not agent.get("agent_running")
                else f"agent 已运行，番茄未运行: {fanqie.get('message')}"
            )
        ),
    }

    hongguo_runtime = {
        "ok": bool(agent.get("agent_running") and hongguo.get("running")),
        "pkg": hongguo.get("pkg"),
        "running": hongguo.get("running"),
        "pid": hongguo.get("pid"),
        "started": hongguo.get("started"),
        "agent_running": agent.get("agent_running"),
        "message": (
            "红果运行时就绪"
            if agent.get("agent_running") and hongguo.get("running")
            else (
                "agent 未运行（红果 Frida 签名也需要）"
                if not agent.get("agent_running")
                else f"红果 App 未运行: {hongguo.get('message')}"
            )
        ),
        "hints": [] if hongguo.get("running") else [f"请打开 {hongguo.get('pkg')}"],
    }

    ok = bool(
        agent.get("agent_running")
        and fanqie.get("running")
        and hongguo.get("running")
    )
    degraded = agent.get("agent_running") and not ok

    return {
        "ok": ok,
        "degraded": degraded,
        "adb_device": agent.get("adb_device"),
        "agent": agent,
        "fanqie_runtime": fanqie_runtime,
        "hongguo_runtime": hongguo_runtime,
        "message": (
            "全部平台运行时就绪（agent + 番茄 + 红果）"
            if ok
            else "部分运行时缺失，书名搜索/App 下载/红果签名可能失败"
        ),
    }


def bootstrap_on_startup() -> dict[str, Any]:
    """服务启动时调用：按配置尝试启动 agent 与各 App，并打日志。"""
    settings = get_settings()
    report = probe_all_runtimes(
        try_start_agent=settings.fanqie_try_start_agent,
        try_start_apps=settings.try_start_platform_apps,
    )

    agent = report.get("agent") or {}
    fr = report.get("fanqie_runtime") or {}
    hr = report.get("hongguo_runtime") or {}

    if report.get("ok"):
        logger.info(
            "平台运行时就绪: device=%s agent=%s fanqie_pid=%s hongguo_pid=%s",
            report.get("adb_device"),
            agent.get("agent_names"),
            fr.get("fanqie_pid"),
            hr.get("pid"),
        )
    else:
        logger.warning(
            "平台运行时未完全就绪: %s | agent=%s fanqie=%s hongguo=%s",
            report.get("message"),
            agent.get("agent_running"),
            fr.get("fanqie_running"),
            hr.get("running"),
        )
        if agent.get("hints"):
            logger.warning("agent hints: %s", agent.get("hints"))
        if not fr.get("fanqie_running"):
            logger.warning("番茄: %s", fr.get("message"))
        if not hr.get("running"):
            logger.warning("红果: %s", hr.get("message"))

    if settings.fanqie_require_runtime and not agent.get("agent_running"):
        raise RuntimeError(
            "REQUIRE_RUNTIME：Frida agent 未运行。"
            f" device={report.get('adb_device')} hints={agent.get('hints')}"
        )
    if settings.require_platform_apps:
        missing = []
        if not fr.get("fanqie_running"):
            missing.append(settings.fanqie_pkg)
        if not hr.get("running"):
            missing.append(settings.hongguo_pkg)
        if missing:
            raise RuntimeError(
                "REQUIRE_PLATFORM_APPS=true 但以下 App 未运行: " + ", ".join(missing)
            )

    return report
