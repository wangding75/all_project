"""启动/健康检查：配置文件与依赖完整性。

与 runtime.py（设备 agent/App）互补：本模块只检查「文件/配置是否齐」，
runtime 检查「设备进程是否跑」。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.config import REPO_ROOT, get_settings

logger = logging.getLogger(__name__)

# 展示用中文标签
_LABELS = {
    "fanqie_config": "番茄会话配置",
    "fanqie_content_key": "番茄内容解密密钥",
    "hongguo_config": "红果会话配置",
    "hongguo_vendor": "红果 vendor 代码",
    "adb": "ADB 连接",
    "frida_agent": "Frida agent (sys_hlpd)",
    "fanqie_app": "番茄 App 进程",
    "hongguo_app": "红果 App 进程",
}


def _cfg_dir() -> Path:
    return REPO_ROOT / "data" / "config"


def _check_json_file(
    path: Path,
    *,
    key: str,
    label: str,
    required_keys: list[str] | None = None,
    required: bool = True,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "key": key,
        "label": label,
        "ok": False,
        "required": required,
        "message": "",
        "hints": [],
        "detail": {"path": str(path)},
    }
    if not path.is_file():
        item["message"] = f"文件不存在: {path.name}"
        item["hints"] = _hints_for(key)
        return item
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        item["message"] = f"JSON 解析失败: {exc}"
        item["hints"] = [f"检查或重新生成 {path}"]
        return item
    if not isinstance(data, dict):
        item["message"] = "配置根节点必须是 JSON 对象"
        return item
    missing = [k for k in (required_keys or []) if k not in data or data.get(k) in (None, "", {})]
    item["detail"]["keys"] = list(data.keys())[:20]
    if missing:
        item["message"] = f"缺少字段: {', '.join(missing)}"
        item["hints"] = _hints_for(key)
        return item
    item["ok"] = True
    item["message"] = "就绪"
    return item


def _hints_for(key: str) -> list[str]:
    mapping = {
        "fanqie_config": [
            "python tools/setup/grab_fanqie_config.py",
            "需模拟器番茄 App + sys_hlpd",
        ],
        "fanqie_content_key": [
            "从设备 mmkv 导出 key 到 data/config/fanqie_content_key.json",
            "见 docs/fanqie_app_content.md",
        ],
        "hongguo_config": [
            "python tools/setup/grab_hongguo_config.py",
            "或从 fanqie_config 复制会话字段（仅开发兜底）",
        ],
        "hongguo_vendor": [
            "git clone --depth 1 https://github.com/zhangbaio/hongguo.git vendor/hongguo",
        ],
        "adb": [
            "adb connect <设备地址>",
            "检查 .env 中 ADB_DEVICE / ADB_PATH",
        ],
        "frida_agent": [
            f"adb shell '{REPO_ROOT}' 下 tools/setup/sys_hlpd push 后启动",
            "或 tools/setup/push_frida.ps1",
        ],
        "fanqie_app": ["在模拟器打开番茄小说 com.dragon.read"],
        "hongguo_app": ["在模拟器打开红果短剧 com.phoenix.read"],
    }
    return mapping.get(key, [])


def check_config_files() -> list[dict[str, Any]]:
    """检查 data/config 与 vendor 文件完整性。"""
    cfg = _cfg_dir()
    items: list[dict[str, Any]] = []

    items.append(
        _check_json_file(
            cfg / "fanqie_config.json",
            key="fanqie_config",
            label=_LABELS["fanqie_config"],
            required_keys=["api_host", "base_query"],
            required=True,
        )
    )
    # 内容密钥：App 解密正文需要；缺则搜索仍可用、下载正文可能失败
    items.append(
        _check_json_file(
            cfg / "fanqie_content_key.json",
            key="fanqie_content_key",
            label=_LABELS["fanqie_content_key"],
            required_keys=["key_b64"],
            required=False,
        )
    )
    items.append(
        _check_json_file(
            cfg / "hongguo_config.json",
            key="hongguo_config",
            label=_LABELS["hongguo_config"],
            required_keys=None,  # 上游字段不统一，有文件即可
            required=True,
        )
    )

    # 红果 vendor
    try:
        from platforms.hongguo.bridge import vendor_ready

        vr = vendor_ready()
        ok = bool(vr.get("ok"))
        items.append(
            {
                "key": "hongguo_vendor",
                "label": _LABELS["hongguo_vendor"],
                "ok": ok,
                "required": True,
                "message": "就绪" if ok else "vendor 不完整或缺失",
                "hints": [] if ok else _hints_for("hongguo_vendor"),
                "detail": vr if isinstance(vr, dict) else {"ok": ok},
            }
        )
    except Exception as exc:  # noqa: BLE001
        items.append(
            {
                "key": "hongguo_vendor",
                "label": _LABELS["hongguo_vendor"],
                "ok": False,
                "required": True,
                "message": str(exc),
                "hints": _hints_for("hongguo_vendor"),
                "detail": {},
            }
        )

    return items


def check_runtime_as_items(runtime_report: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """把 runtime 探测结果展平为 checks 列表。"""
    if runtime_report is None:
        try:
            from platforms.runtime import probe_all_runtimes

            runtime_report = probe_all_runtimes(try_start_agent=False, try_start_apps=False)
        except Exception as exc:  # noqa: BLE001
            return [
                {
                    "key": "device_runtime",
                    "label": "设备运行时",
                    "ok": False,
                    "required": True,
                    "message": str(exc),
                    "hints": _hints_for("adb"),
                    "detail": {},
                }
            ]

    agent = runtime_report.get("agent") or {}
    fr = runtime_report.get("fanqie_runtime") or {}
    hr = runtime_report.get("hongguo_runtime") or {}

    items: list[dict[str, Any]] = []

    adb_ok = bool(agent.get("adb_ok"))
    items.append(
        {
            "key": "adb",
            "label": _LABELS["adb"],
            "ok": adb_ok,
            "required": True,
            "message": f"设备 {agent.get('adb_device') or '?'}" if adb_ok else (agent.get("message") or "ADB 不可用"),
            "hints": [] if adb_ok else (agent.get("hints") or _hints_for("adb")),
            "detail": {"adb_device": agent.get("adb_device"), "adb_ok": adb_ok},
        }
    )

    agent_ok = bool(agent.get("agent_running"))
    items.append(
        {
            "key": "frida_agent",
            "label": _LABELS["frida_agent"],
            "ok": agent_ok,
            "required": True,
            "message": (
                f"运行中: {', '.join(agent.get('agent_names') or [])}"
                if agent_ok
                else (agent.get("message") or "agent 未运行")
            ),
            "hints": [] if agent_ok else (agent.get("hints") or _hints_for("frida_agent")),
            "detail": {
                "agent_names": agent.get("agent_names"),
                "agent_bin": agent.get("agent_bin"),
                "agent_bin_present": agent.get("agent_bin_present"),
            },
        }
    )

    fq_ok = bool(fr.get("fanqie_running"))
    items.append(
        {
            "key": "fanqie_app",
            "label": _LABELS["fanqie_app"],
            "ok": fq_ok,
            "required": True,
            "message": (
                f"pid={fr.get('fanqie_pid')}" if fq_ok else (fr.get("message") or "番茄未运行")
            ),
            "hints": [] if fq_ok else _hints_for("fanqie_app"),
            "detail": {
                "pkg": fr.get("fanqie_pkg") or get_settings().fanqie_pkg,
                "pid": fr.get("fanqie_pid"),
            },
        }
    )

    hg_ok = bool(hr.get("running"))
    items.append(
        {
            "key": "hongguo_app",
            "label": _LABELS["hongguo_app"],
            "ok": hg_ok,
            "required": True,
            "message": f"pid={hr.get('pid')}" if hg_ok else (hr.get("message") or "红果未运行"),
            "hints": [] if hg_ok else _hints_for("hongguo_app"),
            "detail": {"pkg": hr.get("pkg") or get_settings().hongguo_pkg, "pid": hr.get("pid")},
        }
    )

    return items


def build_health_report(
    *,
    include_runtime: bool = True,
    runtime_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """汇总配置 + 运行时检查，供 /health 与启动日志使用。"""
    config_items = check_config_files()
    runtime_items = check_runtime_as_items(runtime_report) if include_runtime else []
    checks = config_items + runtime_items

    required_fail = [c for c in checks if c.get("required") and not c.get("ok")]
    optional_fail = [c for c in checks if not c.get("required") and not c.get("ok")]

    if not required_fail:
        status = "ok"
        if optional_fail:
            status = "degraded"
            summary = f"核心依赖就绪；可选项缺失: {', '.join(c['label'] for c in optional_fail)}"
        else:
            summary = "配置与设备运行时全部就绪"
    else:
        status = "degraded"
        summary = "依赖不完整: " + "；".join(
            f"{c['label']}({c.get('message') or '失败'})" for c in required_fail[:6]
        )

    # 兼容旧 dependencies 字典
    dependencies: dict[str, Any] = {
        "config": {c["key"]: c for c in config_items},
        "runtime_checks": {c["key"]: c for c in runtime_items},
    }
    if runtime_report:
        dependencies["device_runtime"] = {
            "ok": runtime_report.get("ok"),
            "degraded": runtime_report.get("degraded"),
            "adb_device": runtime_report.get("adb_device"),
            "message": runtime_report.get("message"),
            "agent": runtime_report.get("agent"),
        }
        dependencies["fanqie_runtime"] = runtime_report.get("fanqie_runtime") or {}
        dependencies["hongguo_runtime"] = runtime_report.get("hongguo_runtime") or {}

    try:
        from platforms.hongguo.bridge import vendor_ready

        dependencies["hongguo_vendor"] = vendor_ready()
    except Exception as exc:  # noqa: BLE001
        dependencies["hongguo_vendor"] = {"ok": False, "message": str(exc)}

    return {
        "status": status,
        "summary": summary,
        "checks": checks,
        "dependencies": dependencies,
        "required_failed": [c["key"] for c in required_fail],
        "optional_failed": [c["key"] for c in optional_fail],
    }


def log_startup_readiness(report: dict[str, Any] | None = None) -> dict[str, Any]:
    """启动时打日志；不抛错（阻断由 runtime.bootstrap_on_startup 的 require_* 控制）。"""
    if report is None:
        # 启动路径：runtime 已 bootstrap 过则再 probe 一次会重复；这里只查配置文件
        # 完整报告由调用方合并
        report = build_health_report(include_runtime=False)

    status = report.get("status")
    summary = report.get("summary") or ""
    if status == "ok":
        logger.info("配置完整性: %s", summary)
    else:
        logger.warning("配置完整性: %s", summary)
        for c in report.get("checks") or []:
            if not c.get("ok"):
                logger.warning(
                    "  [缺失] %s: %s | hints=%s",
                    c.get("label"),
                    c.get("message"),
                    c.get("hints"),
                )
    return report


def bootstrap_config_on_startup() -> dict[str, Any]:
    """启动时：尝试补齐可自动修复的配置，再检查完整性。"""
    # 红果配置：若缺且 vendor 有 config.json 则复制
    try:
        from platforms.hongguo.bridge import ensure_config

        ensure_config()
        logger.info("红果配置 ensure_config 完成")
    except Exception as exc:  # noqa: BLE001
        logger.warning("红果配置 ensure_config: %s", exc)

    # 开发兜底：hongguo 缺失时尝试从 fanqie_config 复制公共会话字段（不保证可用）
    try:
        _maybe_bootstrap_hongguo_from_fanqie()
    except Exception as exc:  # noqa: BLE001
        logger.debug("hongguo from fanqie bootstrap skipped: %s", exc)

    return log_startup_readiness()


def _maybe_bootstrap_hongguo_from_fanqie() -> None:
    """若仅存在番茄配置，明确提示需单独捕获红果会话。"""
    cfg = _cfg_dir()
    hg = cfg / "hongguo_config.json"
    fq = cfg / "fanqie_config.json"
    if hg.is_file() or not fq.is_file():
        return
    # 不再自动复制（两 App 会话不同）；只打提示
    logger.warning(
        "缺少 hongguo_config.json。请运行: python tools/setup/grab_hongguo_config.py"
    )
