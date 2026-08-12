"""阶段 E0 错误归类映射与 E2E Skip 逻辑单元测试。"""

from __future__ import annotations

import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path

from app.errors import format_platform_error
from app.sign_pool.errors import SignPoolUnavailableError
from platforms.hongguo.bridge import HongguoVendorError


def test_error_mapping_sign_pool() -> None:
    """测试签名池 503 错误映射。"""
    err = SignPoolUnavailableError()
    assert format_platform_error(err) == "签名节点繁忙或不可用，请稍后重试"


def test_error_mapping_vendor() -> None:
    """测试 Vendor 缺失错误映射。"""
    err = HongguoVendorError("missing vendor at vendor/hongguo")
    mapped = format_platform_error(err)
    assert "红果 Vendor 组件未处于就绪状态" in mapped


def test_error_mapping_cookie_expired() -> None:
    """测试 会话/Cookie 失效错误映射。"""
    err = RuntimeError("401 Unauthorized: session expired")
    mapped = format_platform_error(err)
    assert "平台会话或 Cookie 已失效" in mapped


def test_error_mapping_timeout() -> None:
    """测试 网络超时错误映射。"""
    err = RuntimeError("Connection timed out after 30s")
    mapped = format_platform_error(err)
    assert "平台网络请求超时" in mapped


def test_error_mapping_generic() -> None:
    """测试 通用异常规范前缀。"""
    err = ValueError("unknown format")
    mapped = format_platform_error(err)
    assert mapped.startswith("平台 API 访问失败:")


def test_hongguo_runtime_syncs_imported_vendor_adb_path(monkeypatch) -> None:
    """运行时发现的 ADB 路径必须覆盖 vendor 导入时的旧默认值。"""
    import platforms.hongguo.bridge as bridge
    import platforms.hongguo.frida_compat as frida_compat
    import platforms.device_discovery as device_discovery
    import platforms.runtime as runtime

    settings = SimpleNamespace(
        adb_path=r"C:\Android\platform-tools\adb.exe",
        hongguo_pkg="com.phoenix.read",
    )
    vendor = SimpleNamespace(
        ADB=r"D:\Program Files\Netease\MuMu Player 12\shell\adb.exe",
        DEV="",
    )
    reset_calls: list[str] = []

    monkeypatch.setattr("app.config.get_settings", lambda: settings)
    monkeypatch.setattr(
        device_discovery,
        "resolve_rd_test_device",
        lambda **_: SimpleNamespace(serial="127.0.0.1:16416"),
    )
    monkeypatch.setattr(frida_compat, "ensure_compatible", lambda: None)
    monkeypatch.setattr(
        runtime,
        "probe_shared_agent",
        lambda **_: {"agent_running": True},
    )
    monkeypatch.setattr(
        runtime,
        "ensure_app_running",
        lambda *_args, **_kwargs: {"running": True},
    )
    monkeypatch.setattr(bridge, "load_hongguo_api", lambda: vendor)
    monkeypatch.setattr(
        bridge,
        "_reset_local_oracle",
        lambda: reset_calls.append("reset"),
    )

    bridge._ensure_hongguo_runtime()

    assert vendor.ADB == settings.adb_path
    assert vendor.DEV == "127.0.0.1:16416"
    assert reset_calls == ["reset"]


def test_e2e_fanqie_skip_when_no_id() -> None:
    """测试 e2e_fanqie.py 无 ID 时输出 [SKIP] 并 exit 0。"""
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "e2e_fanqie.py"
    proc = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": "server"},
    )
    assert proc.returncode == 0
    assert "[SKIP]" in proc.stdout


def test_e2e_hongguo_skip_when_no_id() -> None:
    """测试 e2e_hongguo.py 无 ID 时输出 [SKIP] 并 exit 0。"""
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "e2e_hongguo.py"
    proc = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": "server"},
    )
    assert proc.returncode == 0
    assert "[SKIP]" in proc.stdout
