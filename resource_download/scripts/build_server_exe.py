"""Build the standalone RD server executable used by a release package."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SPEC_FILE = ROOT_DIR / "RDServer.spec"
OUTPUT_DIR = ROOT_DIR / "dist"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    if not SPEC_FILE.is_file():
        raise SystemExit(f"missing PyInstaller spec: {SPEC_FILE}")

    build_root = Path(tempfile.mkdtemp(prefix="rd-server-build-", dir=str(ROOT_DIR)))
    try:
        dist_dir = build_root / "dist"
        work_dir = build_root / "work"
        command = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--distpath",
            str(dist_dir),
            "--workpath",
            str(work_dir),
            str(SPEC_FILE),
        ]
        env = os.environ.copy()
        # The build must resolve only against this checkout.  Do not carry a
        # caller-provided PYTHONPATH into module collection.
        env.pop("PYTHONPATH", None)
        subprocess.run(command, cwd=str(ROOT_DIR), env=env, check=True)

        built = dist_dir / "RDServer.exe"
        if not built.is_file() or built.stat().st_size < 1024 * 1024:
            raise SystemExit(f"PyInstaller did not produce a valid server executable: {built}")

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        target = OUTPUT_DIR / "RDServer.exe"
        shutil.copy2(built, target)
        print(f"RD_SERVER_EXE={target}")
        print(f"RD_SERVER_SHA256={sha256(target)}")
        print("RD_SERVER_BUILD=PASS")
        return 0
    finally:
        shutil.rmtree(build_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
