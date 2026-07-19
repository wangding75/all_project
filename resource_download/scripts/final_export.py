import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT = Path(r"D:\github\all_project\resource_download")
dist_dir = ROOT / "dist"
dist_dir.mkdir(parents=True, exist_ok=True)

target_exe = dist_dir / "ResourceDownloader.exe"

temp_out = Path(r"C:\Temp\pyi_out")
if temp_out.exists():
    try:
        shutil.rmtree(temp_out, ignore_errors=True)
    except Exception:
        pass
temp_out.mkdir(parents=True, exist_ok=True)

pyinstaller_bin = ROOT / "server" / ".venv" / "Scripts" / "pyinstaller.exe"

cmd = [
    str(pyinstaller_bin),
    "--name=ResourceDownloader",
    "--onefile",
    "--noconsole",
    "--noupx",
    "--clean",
    f"--distpath={temp_out}",
    f"--workpath={temp_out / 'build'}",
    f"--add-data={ROOT / 'ui'};ui",
    f"--add-data={ROOT / 'server' / 'app'};server/app",
    f"--add-data={ROOT / 'vendor'};vendor",
    "--exclude-module=tkinter",
    "--exclude-module=matplotlib",
    "--exclude-module=IPython",
    str(ROOT / "desktop" / "main.py")
]

print(f"[1] Running PyInstaller: {' '.join(cmd)}")
res = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
print(f"[2] PyInstaller Exit Code: {res.returncode}")

built_file = temp_out / "ResourceDownloader.exe"
print(f"[3] Built file exists: {built_file.exists()}")

if built_file.exists():
    size = built_file.stat().st_size
    print(f"[4] Built file size: {size / (1024*1024):.2f} MB")
    print(f"[5] Copying bytes to target: {target_exe}")
    
    with open(built_file, "rb") as f_in:
        data = f_in.read()
    with open(target_exe, "wb") as f_out:
        f_out.write(data)
        f_out.flush()
        os.fsync(f_out.fileno())
    
    print(f"[6] Target file exists after copy: {target_exe.exists()}, size: {target_exe.stat().st_size / (1024*1024):.2f} MB")
else:
    print(f"[ERR] PyInstaller stderr: {res.stderr}")
