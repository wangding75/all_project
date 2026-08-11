"""Hongguo Frida compatibility preflight.

The vendor's Java bridge is tied to Frida 16.x. A mismatched remote server
otherwise fails later with a generic ProtocolError, so collect both sides and
stop with a stable runtime code before importing/attaching the vendor oracle.
"""

from __future__ import annotations

import importlib.metadata
import re
from typing import Any


SUPPORTED_FRIDA_VERSION = "16.7.19"
SUPPORTED_FRIDA_TOOLS_VERSION = "14.10.4"
SUPPORTED_TARGET_ARCHES = {"x86_64", "amd64"}
VERSION_RE = re.compile(r"(?<!\d)(\d+\.\d+\.\d+)(?!\d)")


class FridaCompatibilityError(RuntimeError):
    code = "RUNTIME_INCOMPATIBLE"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(f"{self.code}: {message}")
        self.details = details or {}


def _distribution_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "missing"


def _first_version(value: str) -> str:
    match = VERSION_RE.search(value or "")
    return match.group(1) if match else "unknown"


def _target_info() -> tuple[str, str, str]:
    from platforms.fanqie import device

    device.connect()
    version_result = device.adb("shell", device.agent_bin(), "--version", timeout=8)
    version_text = "\n".join(
        item for item in ((version_result.stdout or ""), (version_result.stderr or "")) if item
    )
    target_version = _first_version(version_text)
    arch_result = device.adb("shell", "getprop", "ro.product.cpu.abi", timeout=8)
    arch = (arch_result.stdout or "").strip().splitlines()[0] if arch_result.stdout else "unknown"
    return target_version, arch, device.adb_device()


def _bridge_probe() -> tuple[str, int | None]:
    """Exercise the same Frida device bridge used by the Hongguo adapter."""

    from platforms.fanqie.device import get_frida_device

    processes = get_frida_device().enumerate_processes()
    return "PASS", len(processes)


def collect_compatibility() -> dict[str, Any]:
    """Collect versions without hiding an unavailable target/runtime."""

    try:
        import frida  # type: ignore

        python_version = str(getattr(frida, "__version__", "")) or _distribution_version("frida")
    except ImportError:
        python_version = "missing"
    tools_version = _distribution_version("frida-tools")
    try:
        target_version, target_arch, adb_device = _target_info()
    except Exception as exc:  # noqa: BLE001 - preflight must report the cause
        target_version = "unavailable"
        target_arch = "unknown"
        adb_device = "unknown"
        return {
            "python_frida": python_version,
            "frida_tools": tools_version,
            "target_frida_server": target_version,
            "target_arch": target_arch,
            "adb_device": adb_device,
            "bridge_result": "NOT_REACHED",
            "bridge_process_count": None,
            "compatible": False,
            "reason": f"unable to inspect target Frida server: {type(exc).__name__}: {exc}",
        }
    versions_and_arch_ok = (
        python_version == SUPPORTED_FRIDA_VERSION
        and tools_version == SUPPORTED_FRIDA_TOOLS_VERSION
        and target_version == SUPPORTED_FRIDA_VERSION
        and target_arch in SUPPORTED_TARGET_ARCHES
    )
    bridge_result = "SKIPPED_VERSION_OR_ARCH_MISMATCH"
    bridge_process_count: int | None = None
    reason = "" if versions_and_arch_ok else "version or architecture mismatch"
    if versions_and_arch_ok:
        try:
            bridge_result, bridge_process_count = _bridge_probe()
        except Exception as exc:  # noqa: BLE001 - expose bridge failures as runtime state
            bridge_result = f"FAIL: {type(exc).__name__}: {exc}"
            reason = "Frida bridge probe failed"
    compatible = versions_and_arch_ok and bridge_result == "PASS"
    return {
        "python_frida": python_version,
        "frida_tools": tools_version,
        "target_frida_server": target_version,
        "target_arch": target_arch,
        "adb_device": adb_device,
        "bridge_result": bridge_result,
        "bridge_process_count": bridge_process_count,
        "compatible": compatible,
        "reason": reason,
    }


def ensure_compatible() -> dict[str, Any]:
    info = collect_compatibility()
    if not info["compatible"]:
        raise FridaCompatibilityError(
            "Frida runtime versions are incompatible; install the pinned host package "
            f"frida=={SUPPORTED_FRIDA_VERSION}, frida-tools=={SUPPORTED_FRIDA_TOOLS_VERSION} "
            f"and target frida-server=={SUPPORTED_FRIDA_VERSION}",
            details=info,
        )
    return info
