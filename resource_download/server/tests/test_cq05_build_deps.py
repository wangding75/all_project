"""CQ-05：路径解析、依赖分层与构建脚本测试套件。"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import pytest

server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

from app.config import get_settings
from app.version import VERSION


def test_no_hardcoded_personal_paths_in_config():
    """验证配置类中的 adb_path 已清理硬编码盘符路径，默认从环境变量或 PATH 读取。"""
    settings = get_settings()
    assert "D:\\" not in settings.adb_path
    assert "C:\\Users\\" not in settings.adb_path
    assert settings.adb_path == "adb"


def test_pyproject_toml_version_sync():
    """验证 pyproject.toml 中的项目版本与 app.version.VERSION 权威源完全一致。"""
    repo_root = Path(__file__).resolve().parents[2]
    toml_path = repo_root / "pyproject.toml"
    assert toml_path.exists()

    content = toml_path.read_text(encoding="utf-8")
    assert f'version = "{VERSION}"' in content


def test_build_script_independency():
    """验证构建脚本 ROOT_DIR 能够独立正确解析仓库根。"""
    scripts_dir = Path(__file__).resolve().parents[2] / "scripts"
    sys.path.insert(0, str(scripts_dir))
    from build_exe import ROOT_DIR  # type: ignore

    assert ROOT_DIR.exists()
    assert (ROOT_DIR / "pyproject.toml").exists()
