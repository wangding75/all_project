import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT = Path(r"D:\github\all_project\resource_download")
dist_dir = ROOT / "dist"
build_dir = ROOT / "build"
dist_dir.mkdir(parents=True, exist_ok=True)
build_dir.mkdir(parents=True, exist_ok=True)

pyinstaller_bin = ROOT / "server" / ".venv" / "Scripts" / "pyinstaller.exe"

cmd = [
    str(pyinstaller_bin),
    "--name=ResourceDownloader",
    "--onefile",
    "--noconsole",
    "--noupx",
    f"--distpath={dist_dir}",
    f"--workpath={build_dir}",
    f"--add-data={ROOT / 'ui'};ui",
    f"--add-data={ROOT / 'server' / 'app'};server/app",
    f"--add-data={ROOT / 'vendor'};vendor",
    "--exclude-module=tkinter",
    "--exclude-module=matplotlib",
    "--exclude-module=IPython",
    str(ROOT / "desktop" / "main.py")
]

print("==================================================")
print("[BUILD] 同步编译包装脚本启动，开始 PyInstaller 打包...")
print("==================================================")

process = subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")

for line in process.stdout:
    print(line, end="")

process.wait()
print(f"\n[BUILD] 打包进程退出代码: {process.returncode}")

exe_path = dist_dir / "ResourceDownloader.exe"
print(f"[CHECK] 最终产物文件校验: {exe_path}")
print(f"[EXISTS]: {exe_path.exists()}")

if exe_path.exists():
    print(f"[FILE SIZE]: {exe_path.stat().st_size / (1024*1024):.2f} MB")
    print("\n==================================================")
    print("打包刷盘完成！请前往 dist 目录查看 ResourceDownloader.exe")
    print("==================================================")
else:
    print("[ERR] 打包未生成目标文件！")
