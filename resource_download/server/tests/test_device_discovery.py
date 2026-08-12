from __future__ import annotations

import json
import subprocess

import pytest

from platforms.device_discovery import DeviceDiscoveryError, discover_rd_test_device, enumerate_mumu_instances


def _manager_script(tmp_path, payload: dict) -> str:
    path = tmp_path / "manager.py"
    path.write_text(
        "import json; print(json.dumps(" + repr(payload) + "))\n",
        encoding="utf-8",
    )
    return str(path)


def test_discovery_selects_by_instance_name_and_endpoint(monkeypatch, tmp_path):
    payload = {
        "0": {
            "index": "0",
            "name": "SX测试",
            "player_state": "start_finished",
            "is_android_started": True,
            "adb_host_ip": "127.0.0.1",
            "adb_port": 16384,
        },
        "1": {
            "index": "1",
            "name": "RD测试",
            "player_state": "start_finished",
            "is_android_started": True,
            "adb_host_ip": "127.0.0.1",
            "adb_port": 16416,
        },
    }
    manager = tmp_path / "manager.cmd"
    manager.write_text("@echo {\"0\":{}}", encoding="utf-8")

    def fake_run(command, **kwargs):
        if command[1:4] == ["info", "--vmindex", "all"]:
            return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")
        if command[1:3] == ["connect", "127.0.0.1:16416"]:
            return subprocess.CompletedProcess(command, 0, "connected", "")
        if command[1:3] == ["devices", "-l"]:
            return subprocess.CompletedProcess(
                command,
                0,
                "List of devices attached\n127.0.0.1:16416 device product:rubens\n",
                "",
            )
        raise AssertionError(command)

    monkeypatch.setattr("platforms.device_discovery._run", fake_run)
    found = discover_rd_test_device(adb="adb", manager="manager")
    assert found.instance_name == "RD测试"
    assert found.serial == "127.0.0.1:16416"


def test_discovery_rejects_wrong_explicit_serial(monkeypatch):
    payload = {
        "1": {
            "index": "1",
            "name": "RD测试",
            "player_state": "start_finished",
            "is_android_started": True,
            "adb_host_ip": "127.0.0.1",
            "adb_port": 16416,
        }
    }

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")

    monkeypatch.setattr("platforms.device_discovery._run", fake_run)
    with pytest.raises(DeviceDiscoveryError, match="does not belong"):
        discover_rd_test_device(adb="adb", manager="manager", explicit_serial="127.0.0.1:7555")


def test_discovery_rejects_ambiguous_instance(monkeypatch):
    payload = {
        "0": {"name": "RD测试", "player_state": "start_finished", "is_android_started": True, "adb_host_ip": "127.0.0.1", "adb_port": 16416},
        "1": {"name": "RD测试", "player_state": "start_finished", "is_android_started": True, "adb_host_ip": "127.0.0.1", "adb_port": 16448},
    }

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")

    monkeypatch.setattr("platforms.device_discovery._run", fake_run)
    with pytest.raises(DeviceDiscoveryError, match="found 2"):
        discover_rd_test_device(adb="adb", manager="manager", validate_adb=False)
