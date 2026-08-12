"""Self-contained release-package smoke test.

The test extracts a RD ZIP to a fresh temporary directory and starts only the
executables and files from that directory.  It deliberately removes
PYTHONPATH and does not add the source checkout to the child environment.
"""

from __future__ import annotations

import argparse
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


REQUIRED_FILES = (
    "ResourceDownloader.exe",
    "RDServer.exe",
    "server/run.py",
    "server/app/__init__.py",
    "server/app/main.py",
    "server/platforms/readiness.py",
    "server/platforms/runtime.py",
    "vendor/hongguo/hongguo.py",
    "vendor/hongguo/offline_dl.py",
    "vendor/hongguo/frida/unwrap_spade.py",
    "config/production.env.example",
    "data/config/fanqie_config.example.json",
    "data/config/hongguo_config.example.json",
    "sdk/license_service_client-1.0.0rc4-py3-none-any.whl",
    "DEPLOYMENT_GUIDE.md",
    "ROLLBACK_GUIDE.md",
    "VERSION_MANIFEST.md",
    "scripts/start_rd_server.ps1",
)


def _forbidden(rel: str) -> str | None:
    lower = rel.lower().replace("\\", "/")
    name = lower.rsplit("/", 1)[-1]
    if lower.endswith((".pyc", ".pyo", ".sqlite", ".sqlite3", ".db", ".pkl")):
        return "runtime/cache artifact"
    if "/__pycache__/" in f"/{lower}/" or lower.startswith("__pycache__/"):
        return "python cache"
    if name in {".env", "config.json", "cookies.json", "session.json", "device_identity.json"}:
        return "runtime secret/config file"
    if any(token in lower for token in ("test-secret", "private-key", "activation-code", "session-secret")):
        return "secret-like filename"
    return None


def _assert_package(zip_path: Path) -> list[str]:
    with zipfile.ZipFile(zip_path) as archive:
        names = sorted(archive.namelist())
        if len(names) != len(set(names)):
            raise RuntimeError("ZIP contains duplicate entries")
        for name in names:
            normalized = name.replace("\\", "/")
            if normalized.startswith("/") or "../" in normalized.split("/"):
                raise RuntimeError(f"ZIP path traversal entry: {name}")
            reason = _forbidden(normalized)
            if reason:
                raise RuntimeError(f"forbidden package entry ({reason}): {name}")
        missing = [item for item in REQUIRED_FILES if item not in names]
        if missing:
            raise RuntimeError("required package files missing: " + ", ".join(missing))
        return names


def _wait_http(url: str, timeout: float = 25.0) -> tuple[int, bytes]:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                return response.status, response.read()
        except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            last_error = exc
            time.sleep(0.25)
    raise RuntimeError(f"endpoint did not become ready: {url}: {last_error}")


def _stop(process: subprocess.Popen[str] | None) -> None:
    if process is None:
        return
    if os.name == "nt":
        # PyInstaller GUI children can survive a normal terminate() call and
        # keep the package SQLite/log files open.  The PID is owned by this
        # smoke process, so terminate its process tree first.
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            pass
        return
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            pass
    if process.poll() is None:
        process.kill()
    if process.poll() is None:
        process.wait(timeout=8)


def _remove_temp_tree(path: Path) -> None:
    last_error: Exception | None = None
    for _ in range(12):
        try:
            shutil.rmtree(path)
            return
        except OSError as exc:
            last_error = exc
            time.sleep(0.5)
    if last_error:
        raise last_error


def _clean_child_env(port: int, state_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    for key in list(env):
        if key.startswith("LICENSE_SERVICE_") or key in {
            "SERVICE_CREDENTIAL_PRIVATE_KEY",
            "MASTER_KEY",
            "DB_PASSWORD",
            "COOKIE",
            "SESSION_SECRET",
        }:
            env.pop(key, None)
    env.update(
        {
            "HOST": "127.0.0.1",
            "PORT": str(port),
            "WORKERS": "1",
            "API_KEY": "package-smoke-" + secrets.token_hex(12),
            "JWT_SECRET": "package-smoke-jwt-" + secrets.token_hex(16),
            "AUTH_MODE": "dual",
            "ADB_DEVICE": "127.0.0.1:7555",
            "PLATFORM_PROBE_ON_STARTUP": "false",
            "FANQIE_PROBE_ON_STARTUP": "false",
            "FANQIE_TRY_START_AGENT": "false",
            "TRY_START_PLATFORM_APPS": "false",
            "REQUIRE_PLATFORM_APPS": "false",
            "SIGN_POOL_ENABLED": "false",
            "LOCALAPPDATA": str(state_dir),
        }
    )
    return env


def _app_import_smoke(package_root: Path, env: dict[str, str]) -> None:
    code = (
        "import sys; "
        f"sys.path.insert(0, {str(package_root / 'server')!r}); "
        "import app; import app.main; print('APP_IMPORT=PASS')"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(package_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0 or "APP_IMPORT=PASS" not in result.stdout:
        raise RuntimeError("package app import failed")


def run(zip_path: Path) -> int:
    names = _assert_package(zip_path)
    temp_root = Path(tempfile.mkdtemp(prefix="rd-package-smoke-"))
    try:
        package_root = temp_root / "package"
        package_root.mkdir()
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(package_root)

        state_dir = temp_root / "state"
        state_dir.mkdir()
        env = _clean_child_env(18081, state_dir)
        _app_import_smoke(package_root, env)

        server: subprocess.Popen[str] | None = None
        client: subprocess.Popen[str] | None = None
        try:
            server = subprocess.Popen(
                [str(package_root / "RDServer.exe")],
                cwd=str(package_root),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            status, _ = _wait_http("http://127.0.0.1:18081/health")
            if status != 200:
                raise RuntimeError(f"RD server health returned HTTP {status}")
            if server.poll() is not None:
                raise RuntimeError("RDServer.exe exited after health check")

            client_env = dict(env)
            client_env.update(
                {
                    "CLIENT_MODE": "thin",
                    "API_BASE": "http://127.0.0.1:18081",
                }
            )
            client = subprocess.Popen(
                [str(package_root / "ResourceDownloader.exe")],
                cwd=str(package_root),
                env=client_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            time.sleep(4)
            if client.poll() is not None:
                raise RuntimeError("ResourceDownloader.exe exited during package smoke")
            print(f"PACKAGE_FILE_COUNT={len(names)}")
            print("APP_IMPORT=PASS")
            print("RD_SERVER_HEALTH=PASS")
            print("RD_CLIENT_START=PASS")
            print("PACKAGE_SMOKE=PASS")
            return 0
        finally:
            _stop(client)
            _stop(server)
    finally:
        # WebView2 may outlive the parent client briefly on Windows; remove
        # the complete isolated state only after its lock is released.
        _remove_temp_tree(temp_root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip", type=Path)
    args = parser.parse_args()
    try:
        return run(args.zip.resolve())
    except Exception as exc:  # noqa: BLE001
        print(f"PACKAGE_SMOKE=FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
