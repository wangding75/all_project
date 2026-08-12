"""一键全量质量门禁与校验入口 (CQ-06)。"""

from __future__ import annotations

import os
import sys
import py_compile
import subprocess
import hashlib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "server"))
LICENSE_SDK_WHEEL = ROOT_DIR / "vendor" / "license_service_client-1.0.0rc4-py3-none-any.whl"
LICENSE_SDK_SHA256 = "62E502DC2BAB6F925DACB4A51E92D4D39F9CD459E7C209C618C8FB46CC5C29C9"


def run_phase(name: str, fn):
    print(f"\n[QualityGate] Phase: {name} ...")
    try:
        fn()
        print(f"[QualityGate] Phase: {name} -> PASS [OK]")
    except Exception as exc:
        print(f"[QualityGate] Phase: {name} -> FAILED [FAIL] Error: {exc}")
        sys.exit(1)


def check_python_compile():
    """Phase 1: Python 编译与语法错误检查"""
    py_files = list(ROOT_DIR.glob("**/*.py"))
    for py_file in py_files:
        if ".pytest_cache" in str(py_file) or "venv" in str(py_file) or "build" in str(py_file) or "dist" in str(py_file):
            continue
        try:
            py_compile.compile(str(py_file), doraise=True)
        except py_compile.PyCompileError as e:
            raise RuntimeError(f"Python 编译错误在文件: {py_file}: {e}") from e


def check_version_consistency():
    """Phase 2: 全链路权威版本一致性检查"""
    from app.version import VERSION, __version__
    assert VERSION == "1.0.0", f"VERSION 不是 1.0.0: {VERSION}"
    assert __version__ == VERSION, f"__version__ 不一致: {__version__}"

    toml_path = ROOT_DIR / "pyproject.toml"
    assert toml_path.exists(), "缺少 pyproject.toml"
    content = toml_path.read_text(encoding="utf-8")
    assert f'version = "{VERSION}"' in content, f"pyproject.toml 中版本未匹配 {VERSION}"


def check_single_worker_constraint():
    """Phase 3: WORKERS=1 单进程/单 Worker 运行约束检查"""
    from app.config import get_settings
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.workers == 1, f"WORKERS 必须为 1，当前为 {settings.workers}"


def check_dependency_layering():
    """Phase 4: 依赖分层与配置文件校验"""
    req_prod = ROOT_DIR / "requirements.txt"
    req_dev = ROOT_DIR / "requirements-dev.txt"
    assert req_prod.exists(), "缺少 requirements.txt"
    assert req_dev.exists(), "缺少 requirements-dev.txt"
    prod_content = req_prod.read_text(encoding="utf-8").lower()
    dev_content = req_dev.read_text(encoding="utf-8").lower()
    for dependency in ("requests", "bcrypt"):
        assert dependency in prod_content, f"生产依赖缺少 {dependency}"
    assert "pywebview" in dev_content, "桌面构建依赖缺少 pywebview"
    assert "license_service_client" in dev_content, "开发依赖缺少固定 License Service SDK"
    assert LICENSE_SDK_WHEEL.is_file(), f"缺少固定 License SDK Wheel: {LICENSE_SDK_WHEEL}"
    actual = hashlib.sha256(LICENSE_SDK_WHEEL.read_bytes()).hexdigest().upper()
    assert actual == LICENSE_SDK_SHA256, (
        f"License SDK Wheel SHA-256 不匹配: expected={LICENSE_SDK_SHA256}, actual={actual}"
    )
    assert "license_service_client" in prod_content, "生产依赖缺少固定 License Service SDK"
    pyproject = (ROOT_DIR / "pyproject.toml").read_text(encoding="utf-8")
    assert "license_service_client-1.0.0rc4-py3-none-any.whl" in pyproject
    assert LICENSE_SDK_SHA256 in pyproject


def run_pytest_suite():
    """Phase 5: 全量 pytest 自动化测试套件回归"""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT_DIR / "server"), str(ROOT_DIR)))
    # 防止 test_quality_gate_execution -> quality_gate -> pytest 无限递归。
    env["QUALITY_GATE_ACTIVE"] = "1"
    cmd = [sys.executable, "-m", "pytest", "server/tests", "client/tests"]
    result = subprocess.run(cmd, cwd=str(ROOT_DIR), env=env)
    if result.returncode != 0:
        raise RuntimeError(f"pytest 自动化测试套件存在失败, exit_code={result.returncode}")


def main():
    print("==================================================")
    print("      RESOURCE DOWNLOADER QUALITY GATE (CQ-06)    ")
    print("==================================================")

    run_phase("1. Python 语法编译校验", check_python_compile)
    run_phase("2. 权威版本源一致性校验", check_version_consistency)
    run_phase("3. WORKERS=1 单进程约束校验", check_single_worker_constraint)
    run_phase("4. 依赖分层文件校验", check_dependency_layering)
    run_phase("5. pytest 全量自动化测试回归", run_pytest_suite)

    print("\n==================================================")
    print(" ALL QUALITY GATE PHASES PASSED SUCCESSFULLY! ")
    print("==================================================")


if __name__ == "__main__":
    main()
