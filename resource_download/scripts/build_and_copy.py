import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT_DIR = Path(r"D:\github\all_project\resource_download")
dist_dir = ROOT_DIR / "dist"
build_dir = ROOT_DIR / "build"
ui_dir = ROOT_DIR / "client" / "ui"
if not ui_dir.is_dir():
    ui_dir = ROOT_DIR / "ui"
server_app_dir = ROOT_DIR / "server" / "app"
vendor_dir = ROOT_DIR / "vendor"
main_py = ROOT_DIR / "desktop" / "main.py"
venv_py = ROOT_DIR / "server" / ".venv" / "Scripts" / "python.exe"

dist_dir.mkdir(parents=True, exist_ok=True)
build_dir.mkdir(parents=True, exist_ok=True)

cmd = [
    str(venv_py),
    "-m", "PyInstaller",
    "--name=ResourceDownloader",
    "--onefile",
    "--noconsole",
    "--noupx",
    "--clean",
    f"--distpath={dist_dir}",
    f"--workpath={build_dir}",
    f"--add-data={ui_dir};ui",
    f"--add-data={server_app_dir};server/app",
    f"--add-data={vendor_dir};vendor",
    "--exclude-module=tkinter",
    "--exclude-module=matplotlib",
    "--exclude-module=IPython",
    str(main_py)
]

print(f"[BUILD] Executing: {' '.join(cmd)}")
res = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True)
print(f"[EXIT CODE]: {res.returncode}")

exe_file = dist_dir / "ResourceDownloader.exe"
print(f"[CHECK] Target file: {exe_file}")
print(f"[EXISTS]: {exe_file.exists()}")

if exe_file.exists():
    print(f"[SIZE]: {exe_file.stat().st_size / (1024*1024):.2f} MB")
