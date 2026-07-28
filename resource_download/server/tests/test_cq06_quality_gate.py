"""CQ-06：一键全量质量门禁测试套件。"""

from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path
import pytest

server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)


def test_quality_gate_script_exists():
    """验证 scripts/quality_gate.py 脚本存在。"""
    repo_root = Path(__file__).resolve().parents[2]
    gate_script = repo_root / "scripts" / "quality_gate.py"
    assert gate_script.exists()


def test_quality_gate_execution():
    """验证运行 quality_gate.py 全部关卡均通过 (returncode == 0)。"""
    if os.environ.get("QUALITY_GATE_ACTIVE") == "1":
        pytest.skip("quality gate 子测试集中跳过自递归执行")
    repo_root = Path(__file__).resolve().parents[2]
    gate_script = repo_root / "scripts" / "quality_gate.py"

    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "server")
    res = subprocess.run([sys.executable, str(gate_script)], cwd=str(repo_root), env=env, capture_output=True, text=True)

    assert res.returncode == 0, f"Quality gate failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    assert "ALL QUALITY GATE PHASES PASSED SUCCESSFULLY" in res.stdout
