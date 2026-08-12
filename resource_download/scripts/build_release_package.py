"""Build a complete, self-contained T47 RD release package.

This is the only supported RD release assembly path.  It builds both the thin
desktop client and the standalone server, then copies a curated runtime tree
and safe templates into a fresh staging directory before creating the ZIP.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RD_VERSION = "1.0.0"
RELEASE_NAME = "T47"
PACKAGE_NAME = f"RD-{RD_VERSION}-{RELEASE_NAME}.zip"
LICENSE_PACKAGE_NAME = f"LicenseService-1.0.0-rc2-{RELEASE_NAME}.zip"

VENDOR_TOP_LEVEL = (
    "hongguo.py",
    "safeguards.py",
    "downloader.py",
    "devicepool.py",
    "offline_dl.py",
)
VENDOR_FRIDA = (
    "oracle.js",
    "oracle.py",
    "offline_decrypt.py",
    "unwrap_spade.py",
    "decutil.py",
    "extract_keybox_pairs.py",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str], *, cwd: Path = ROOT_DIR) -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    subprocess.run(command, cwd=str(cwd), env=env, check=True)


def git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(ROOT_DIR),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def tracked_files(prefix: str) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--", prefix],
        cwd=str(ROOT_DIR),
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT_DIR / item for item in result.stdout.splitlines() if item.strip()]


def copy_file(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def copy_tracked_tree(prefix: str, destination_root: Path) -> int:
    count = 0
    for source in tracked_files(prefix):
        relative = source.relative_to(ROOT_DIR)
        parts = {part.lower() for part in relative.parts}
        if "tests" in parts or "test" in source.name.lower() or source.name.lower() == "mock_node.py":
            continue
        if "__pycache__" in parts or source.suffix.lower() in {".pyc", ".pyo"}:
            continue
        prefix_parts = len(Path(prefix).parts)
        copy_file(source, destination_root / Path(*relative.parts[prefix_parts:]))
        count += 1
    return count


def copy_curated_vendor(destination_root: Path) -> int:
    source_root = ROOT_DIR / "vendor" / "hongguo"
    count = 0
    for name in VENDOR_TOP_LEVEL:
        copy_file(source_root / name, destination_root / name)
        count += 1
    for name in VENDOR_FRIDA:
        copy_file(source_root / "frida" / name, destination_root / "frida" / name)
        count += 1
    return count


def forbidden_package_path(relative: Path) -> str | None:
    lower = relative.as_posix().lower()
    name = relative.name.lower()
    if lower.endswith((".pyc", ".pyo", ".sqlite", ".sqlite3", ".db", ".pkl")):
        return "runtime/cache artifact"
    if "__pycache__" in relative.parts:
        return "python cache"
    if name in {".env", "config.json", "cookies.json", "session.json", "device_identity.json"}:
        return "runtime secret/config file"
    if any(token in lower for token in ("test-secret", "private-key", "activation-code", "session-secret")):
        return "secret-like filename"
    return None


def audit_package_tree(package_root: Path) -> list[Path]:
    files = sorted(path for path in package_root.rglob("*") if path.is_file())
    for path in files:
        reason = forbidden_package_path(path.relative_to(package_root))
        if reason:
            raise RuntimeError(f"forbidden package file ({reason}): {path}")
    return files


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def assemble_package(package_root: Path) -> dict[str, object]:
    package_root.mkdir(parents=True, exist_ok=True)
    copy_file(ROOT_DIR / "dist" / "ResourceDownloader.exe", package_root / "ResourceDownloader.exe")
    copy_file(ROOT_DIR / "dist" / "RDServer.exe", package_root / "RDServer.exe")

    server_count = copy_tracked_tree("server", package_root / "server")
    ui_count = copy_tracked_tree("client/ui", package_root / "client/ui")
    vendor_count = copy_curated_vendor(package_root / "vendor" / "hongguo")

    # Keep the SDK artifact inside the package so the raw runtime profile can
    # be audited and installed without reaching into the checkout.
    sdk = ROOT_DIR / "vendor" / "license_service_client-1.0.0rc4-py3-none-any.whl"
    copy_file(sdk, package_root / "sdk" / sdk.name)

    copy_file(ROOT_DIR / "docs" / "production.env.example", package_root / "config" / "production.env.example")
    copy_file(
        ROOT_DIR / "vendor" / "hongguo" / "config.example.json",
        package_root / "data" / "config" / "hongguo_config.example.json",
    )
    copy_file(ROOT_DIR / "data" / "sign_pool.example.json", package_root / "data" / "sign_pool.example.json")
    write_json(
        package_root / "data" / "config" / "fanqie_config.example.json",
        {
            "api_host": "https://example.invalid",
            "base_query": "",
            "cookie": "",
            "token": "",
        },
    )

    for relative in (
        "docs/release_package_deployment.md",
        "docs/release_package_rollback.md",
        "runtime/RUNTIME_REQUIREMENTS.md",
        "scripts/package_smoke.py",
        "scripts/start_rd_server.ps1",
        "scripts/stop_rd_server.ps1",
        "scripts/smoke_health.ps1",
        "scripts/push_frida_package.ps1",
        "scripts/rd_server_entry.py",
    ):
        source = ROOT_DIR / relative
        target_name = {
            "docs/release_package_deployment.md": "DEPLOYMENT_GUIDE.md",
            "docs/release_package_rollback.md": "ROLLBACK_GUIDE.md",
        }.get(relative, relative)
        copy_file(source, package_root / target_name)

    agent = ROOT_DIR / "tools" / "setup" / "sys_hlpd"
    if not agent.is_file():
        raise RuntimeError(
            "missing Frida agent tools/setup/sys_hlpd; run the pinned RD agent setup before packaging"
        )
    copy_file(agent, package_root / "runtime" / "sys_hlpd")

    files = audit_package_tree(package_root)
    metadata = {
        "release": RELEASE_NAME,
        "rd_version": RD_VERSION,
        "source_head": git_head(),
        "architecture": "standalone RDServer.exe + thin ResourceDownloader.exe",
        "package_file_count": len(files),
        "server_tracked_file_count": server_count,
        "client_ui_file_count": ui_count,
        "curated_hongguo_file_count": vendor_count,
        "resource_downloader_sha256": sha256(package_root / "ResourceDownloader.exe"),
        "rd_server_sha256": sha256(package_root / "RDServer.exe"),
        "frida_agent_sha256": sha256(package_root / "runtime" / "sys_hlpd"),
        "required_runtime": [
            "server/app",
            "server/platforms",
            "vendor/hongguo",
            "runtime/sys_hlpd",
            "data/config/*.example.json",
        ],
    }
    manifest_path = package_root / "VERSION_MANIFEST.md"
    # Add the manifest, then rewrite it with the final count including itself.
    manifest_path.write_text(f"# RD {RELEASE_NAME} Package Manifest\n", encoding="utf-8")
    files = audit_package_tree(package_root)
    metadata["package_file_count"] = len(files)
    manifest_path.write_text(
        f"# RD {RELEASE_NAME} Package Manifest\n\n"
        f"- Release: {RELEASE_NAME}\n- RD version: {RD_VERSION}\n"
        f"- RD source HEAD: `{metadata['source_head']}`\n"
        f"- Architecture: `{metadata['architecture']}`\n"
        f"- Package file count: {metadata['package_file_count']}\n"
        f"- Server tracked files: {server_count}\n"
        f"- Client UI files: {ui_count}\n"
        f"- Curated Hongguo files: {vendor_count}\n"
        f"- ResourceDownloader.exe SHA256: `{metadata['resource_downloader_sha256']}`\n"
        f"- RDServer.exe SHA256: `{metadata['rd_server_sha256']}`\n"
        f"- Frida agent SHA256: `{metadata['frida_agent_sha256']}`\n\n"
        "The ZIP contains the production server runtime, platform adapters, "
        "curated vendor runtime, startup/smoke/rollback documentation, safe "
        "configuration templates, and no deployment secrets.\n",
        encoding="utf-8",
    )
    audit_package_tree(package_root)
    return metadata


def zip_package(package_root: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
        for path in sorted(package_root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(package_root).as_posix())


def release_files(release_root: Path) -> list[Path]:
    return sorted(path for path in release_root.rglob("*") if path.is_file())


def write_sha256sums(release_root: Path) -> None:
    lines = []
    for path in release_files(release_root):
        relative = path.relative_to(release_root).as_posix()
        if relative == "SHA256SUMS.txt":
            continue
        lines.append(f"{sha256(path)}  {relative}")
    (release_root / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_release(release_root: Path, license_package: Path) -> dict[str, object]:
    if release_root.exists():
        raise RuntimeError(f"release directory already exists; refusing to overwrite: {release_root}")
    if not license_package.is_file():
        raise FileNotFoundError(license_package)

    run([sys.executable, "scripts/build_exe.py", "--noconsole"])
    run([sys.executable, "scripts/build_server_exe.py"])

    package_root = release_root / "rd"
    metadata = assemble_package(package_root)
    release_packages = release_root / "packages"
    release_packages.mkdir(parents=True, exist_ok=True)
    rd_zip = release_packages / PACKAGE_NAME
    zip_package(package_root, rd_zip)
    ls_zip = release_packages / LICENSE_PACKAGE_NAME
    copy_file(license_package, ls_zip)

    rd_hash = sha256(rd_zip)
    ls_hash = sha256(ls_zip)
    release_root.mkdir(parents=True, exist_ok=True)
    (release_root / "RELEASE_MANIFEST.md").write_text(
        f"# {RELEASE_NAME} Release Manifest\n\n"
        "## Release decision\n\n"
        "This is the T47 RC deployment verification. The License Service artifact "
        "is intentionally unchanged at `1.0.0-rc2`; the RD package is the T47 artifact.\n\n"
        f"- RD version: `{RD_VERSION}`\n"
        f"- RD source HEAD: `{metadata['source_head']}`\n"
        "- License Service version: `1.0.0-rc2`\n"
        "- License Service source HEAD: `aa296179016d73471501bb52ef4743460dfe679c`\n"
        f"- RD package: `packages/{PACKAGE_NAME}`\n"
        f"- RD package SHA256: `{rd_hash}`\n"
        f"- License Service package: `packages/{LICENSE_PACKAGE_NAME}`\n"
        f"- License Service package SHA256: `{ls_hash}`\n"
        f"- RD package file count: {metadata['package_file_count']}\n"
        "- Package architecture: `RDServer.exe` standalone server + thin client\n"
        "- Package integrity scope: ZIP entries, required-file audit, forbidden-file audit, SHA256SUMS\n",
        encoding="utf-8",
    )
    (release_root / "RELEASE_ACCEPTANCE_SUMMARY.md").write_text(
        f"# {RELEASE_NAME} Release Acceptance Summary\n\n"
        "Build and package assembly completed.  The formal package smoke and "
        "full deployment gate are recorded after they run against this exact ZIP.\n\n"
        "- RD build: PASS\n"
        "- RD package assembly: PASS\n"
        "- Required-file audit: PASS\n"
        "- Forbidden-file/secret audit: PASS\n"
        "- Package smoke: PENDING\n"
        "- Full T47 re-run: PENDING\n",
        encoding="utf-8",
    )
    write_sha256sums(release_root)
    return {
        "release_root": str(release_root),
        "rd_zip": str(rd_zip),
        "rd_sha256": rd_hash,
        "license_zip": str(ls_zip),
        "license_sha256": ls_hash,
        "rd_head": metadata["source_head"],
        "rd_file_count": metadata["package_file_count"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--license-package", type=Path, required=True)
    parser.add_argument("--release-root", type=Path)
    args = parser.parse_args()
    timestamp = datetime.now(timezone.utc).astimezone().strftime("%Y%m%d_%H%M%S")
    release_root = (args.release_root or (ROOT_DIR.parent.parent / f"{RELEASE_NAME}_RELEASE_{timestamp}")).resolve()
    result = build_release(release_root, args.license_package.resolve())
    for key, value in result.items():
        print(f"{key.upper()}={value}")
    print("RELEASE_PACKAGE_BUILD=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
