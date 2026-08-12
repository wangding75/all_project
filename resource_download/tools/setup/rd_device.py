"""Resolve the named RD MuMu instance for setup/attach scripts."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "server"
if str(SERVER) not in sys.path:
    sys.path.insert(0, str(SERVER))

from platforms.device_discovery import discover_rd_test_device  # noqa: E402


def resolve_device() -> str:
    # ADB_DEVICE can be an operator-supplied assertion on the first call. Once
    # this helper has resolved it, RD_TEST_ADB_SERIAL marks it as discovered;
    # later calls must rediscover after a MuMu restart instead of asserting the
    # stale previous port.
    explicit = "" if os.environ.get("RD_TEST_ADB_SERIAL") else os.environ.get("ADB_DEVICE", "")
    device = discover_rd_test_device(
        adb=os.environ.get("ADB", "adb"),
        instance_name=os.environ.get("MUMU_INSTANCE_NAME", "RD测试"),
        explicit_serial=explicit,
        manager=os.environ.get("MUMU_MANAGER_PATH") or None,
    )
    os.environ["ADB_DEVICE"] = device.serial
    os.environ["RD_TEST_INSTANCE_NAME"] = device.instance_name
    os.environ["RD_TEST_ADB_SERIAL"] = device.serial
    return device.serial
