"""Fail-closed discovery of the RD MuMu instance.

MuMu ADB ports are ephemeral. The instance name reported by MuMuManager is
the identity boundary; a port is never used to decide RD versus SX.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_INSTANCE_NAME = "RD测试"
_CACHE_TTL_SECONDS = 2.0
_cache_lock = threading.RLock()
_cached: "DiscoveredDevice | None" = None
_cached_at = 0.0


class DeviceDiscoveryError(RuntimeError):
    """Raised when the requested MuMu instance cannot be identified safely."""


@dataclass(frozen=True)
class MuMuInstance:
    index: str
    name: str
    state: str
    host: str
    port: int
    raw: dict[str, Any]

    @property
    def serial(self) -> str:
        return f"{self.host}:{self.port}"


@dataclass(frozen=True)
class DiscoveredDevice:
    instance_name: str
    index: str
    serial: str
    host: str
    port: int
    state: str
    adb_devices_line: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "instance_name": self.instance_name,
            "index": self.index,
            "serial": self.serial,
            "host": self.host,
            "port": self.port,
            "state": self.state,
            "adb_devices_line": self.adb_devices_line,
        }


def _manager_candidates() -> list[str]:
    candidates: list[str] = []
    configured = os.environ.get("MUMU_MANAGER_PATH", "").strip()
    if configured:
        candidates.append(configured)
    which = shutil.which("MuMuManager.exe") or shutil.which("MuMuManager")
    if which:
        candidates.append(which)
    for root in (os.environ.get("ProgramFiles", r"C:\Program Files"), r"C:\Program Files"):
        candidates.append(str(Path(root) / "Netease" / "MuMu Player 12" / "shell" / "MuMuManager.exe"))
    return list(dict.fromkeys(candidates))


def manager_path() -> str:
    for candidate in _manager_candidates():
        if Path(candidate).is_file():
            return candidate
    raise DeviceDiscoveryError(
        "MuMuManager.exe was not found; refusing to select an ADB device by port. "
        "Set MUMU_MANAGER_PATH to the installed MuMuManager.exe."
    )


def _run(command: list[str], *, timeout: float = 15.0) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except OSError as exc:
        raise DeviceDiscoveryError(f"failed to run {Path(command[0]).name}: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise DeviceDiscoveryError(f"timed out running {Path(command[0]).name}") from exc


def _parse_manager_json(output: str) -> dict[str, Any]:
    start = output.find("{")
    if start < 0:
        raise DeviceDiscoveryError(f"MuMuManager info returned no JSON: {output.strip()[-300:]}")
    try:
        value = json.loads(output[start:])
    except json.JSONDecodeError as exc:
        raise DeviceDiscoveryError(f"invalid MuMuManager info JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise DeviceDiscoveryError("MuMuManager info JSON is not an object")
    return value


def enumerate_mumu_instances(*, manager: str | None = None, instance_name: str | None = None) -> list[MuMuInstance]:
    manager = manager or manager_path()
    last_error: DeviceDiscoveryError | None = None
    result: subprocess.CompletedProcess[str] | None = None
    for attempt in range(3):
        try:
            result = _run([manager, "info", "--vmindex", "all"])
            if result.returncode == 0:
                break
            last_error = DeviceDiscoveryError(
                f"MuMuManager info failed: {(result.stderr or result.stdout).strip()[-500:]}"
            )
        except DeviceDiscoveryError as exc:
            last_error = exc
        if attempt < 2:
            time.sleep(0.5 * (attempt + 1))
    if result is None or result.returncode != 0:
        raise last_error or DeviceDiscoveryError("MuMuManager info failed")
    payload = _parse_manager_json(result.stdout)
    instances: list[MuMuInstance] = []
    for key, raw in payload.items():
        if not isinstance(raw, dict):
            continue
        raw_name = str(raw.get("name", ""))
        try:
            host = str(raw["adb_host_ip"])
            port = int(raw["adb_port"])
            name = str(raw["name"])
            index = str(raw.get("index", key))
            state = str(raw.get("player_state", ""))
        except (KeyError, TypeError, ValueError) as exc:
            # MuMu reports stopped/transitioning non-target instances with a
            # name but without an ADB endpoint. They are not candidates. A
            # target instance in that state must still fail closed.
            if instance_name and raw_name != instance_name:
                continue
            raise DeviceDiscoveryError(f"MuMuManager returned incomplete metadata for {key}") from exc
        instances.append(MuMuInstance(index=index, name=name, state=state, host=host, port=port, raw=raw))
    return instances


def _adb_devices(adb: str) -> dict[str, str]:
    result = _run([adb, "devices", "-l"])
    if result.returncode != 0:
        raise DeviceDiscoveryError(f"adb devices failed: {(result.stderr or result.stdout).strip()[-500:]}")
    devices: dict[str, str] = {}
    for line in result.stdout.splitlines():
        fields = line.split()
        if fields and fields[0] not in {"List", "*"} and len(fields) >= 2:
            devices[fields[0]] = line
    return devices


def _assert_adb_ready(adb: str, instance: MuMuInstance) -> str:
    _run([adb, "connect", instance.serial], timeout=20.0)
    line = _adb_devices(adb).get(instance.serial, "")
    if not line or line.split()[1:2] != ["device"]:
        raise DeviceDiscoveryError(
            f"MuMu instance {instance.name!r} maps to {instance.serial}, but ADB is not ready: {line or 'missing'}"
        )
    return line


def discover_rd_test_device(
    *,
    adb: str = "adb",
    instance_name: str = DEFAULT_INSTANCE_NAME,
    explicit_serial: str = "",
    manager: str | None = None,
    validate_adb: bool = True,
) -> DiscoveredDevice:
    # MuMuManager can briefly publish a name without its endpoint while a VM
    # is booting or after ADB restarts. Retry that transient state, but still
    # fail closed once the bounded retry window expires.
    last_error: DeviceDiscoveryError | None = None
    instances: list[MuMuInstance] = []
    for attempt in range(5):
        try:
            instances = enumerate_mumu_instances(manager=manager, instance_name=instance_name)
            break
        except DeviceDiscoveryError as exc:
            last_error = exc
            if "incomplete metadata" not in str(exc) or attempt == 4:
                raise
            time.sleep(0.5 * (attempt + 1))
    else:
        raise last_error or DeviceDiscoveryError("MuMuManager discovery failed")
    matches = [item for item in instances if item.name == instance_name]
    if len(matches) != 1:
        names = ", ".join(f"{item.name}={item.serial} ({item.state})" for item in instances) or "none"
        raise DeviceDiscoveryError(
            f"expected exactly one running MuMu instance named {instance_name!r}; found {len(matches)}. Instances: {names}"
        )
    instance = matches[0]
    if instance.state != "start_finished" or not bool(instance.raw.get("is_android_started", False)):
        raise DeviceDiscoveryError(f"MuMu instance {instance_name!r} is not ready: state={instance.state!r}")
    explicit_serial = explicit_serial.strip()
    if explicit_serial and explicit_serial != instance.serial:
        raise DeviceDiscoveryError(
            f"explicit ADB_DEVICE {explicit_serial!r} does not belong to {instance_name!r}; "
            f"manager reports {instance.serial!r}"
        )
    line = _assert_adb_ready(adb, instance) if validate_adb else ""
    return DiscoveredDevice(instance_name, instance.index, instance.serial, instance.host, instance.port, instance.state, line)


def resolve_rd_test_device(*, force: bool = False, settings: Any | None = None) -> DiscoveredDevice:
    global _cached, _cached_at
    if settings is None:
        from app.config import get_settings

        settings = get_settings()
    now = time.monotonic()
    with _cache_lock:
        if not force and _cached is not None and now - _cached_at < _CACHE_TTL_SECONDS:
            return _cached
        device = discover_rd_test_device(
            adb=str(settings.adb_path or "adb"),
            instance_name=str(getattr(settings, "mumu_instance_name", "") or DEFAULT_INSTANCE_NAME),
            explicit_serial=str(getattr(settings, "adb_device", "") or ""),
            manager=str(getattr(settings, "mumu_manager_path", "") or "") or None,
        )
        _cached, _cached_at = device, now
        return device


def clear_cached_device() -> None:
    global _cached, _cached_at
    with _cache_lock:
        _cached, _cached_at = None, 0.0
