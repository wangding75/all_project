"""
PyInstaller 解决 Windows UAC VirtualStore 虚拟化重定向的打包与强行写入脚本
1. 在 Temp 临时构建目录中通过 PyInstaller 进行无 UPX 的打包
2. 使用 Python shutil 文件流 API 强制将生成的 ResourceDownloader.exe 写入目标 dist 目录
"""

import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def run_build():
    print("==================================================")
    print("BUILD: Starting packaging with VirtualStore bypass...")
    print("==================================================")

    entry_script = ROOT_DIR / "desktop" / "main.py"
    ui_dir = ROOT_DIR / "ui"
    server_app_dir = ROOT_DIR / "server" / "app"
    vendor_dir = ROOT_DIR / "vendor"
    
    # 目标 dist 目录
    target_dist = ROOT_DIR / "dist"
    target_dist.mkdir(parents=True, exist_ok=True)

    # 建立隔离的临时构建目录
    temp_dir = Path(tempfile.mkdtemp(prefix="pyi_build_"))
    temp_dist = temp_dir / "dist"
    temp_work = temp_dir / "work"
    temp_dist.mkdir(parents=True, exist_ok=True)
    temp_work.mkdir(parents=True, exist_ok=True)

    pyinstaller_args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=ResourceDownloader",
        "--onefile",
        "--noconsole",
        "--noupx",
        "--clean",
        f"--distpath={temp_dist}",
        f"--workpath={temp_work}",
        f"--add-data={ui_dir}{os.pathsep}ui",
        f"--add-data={server_app_dir}{os.pathsep}server/app",
        "--exclude-module=tkinter",
        "--exclude-module=matplotlib",
        "--exclude-module=IPython",
    ]

    if vendor_dir.exists():
        pyinstaller_args.append(f"--add-data={vendor_dir}{os.pathsep}vendor")

    pyinstaller_args.append(str(entry_script))

    print(f"[CMD] Executing PyInstaller in temp dir: {temp_dir}")

    try:
        subprocess.run(pyinstaller_args, cwd=str(ROOT_DIR), check=True)
        
        # 查找临时目录或 VirtualStore 中的产物
        produced_exe = temp_dist / "ResourceDownloader.exe"
        if not produced_exe.exists():
            vstore = Path(r"C:\Users\wangding\AppData\Local\VirtualStore") / str(temp_dist).replace(":", "")
            vstore_exe = vstore / "ResourceDownloader.exe"
            if vstore_exe.exists():
                produced_exe = vstore_exe

        print(f"[SEARCH] 找寻到的 EXE 产物: {produced_exe}, 存在: {produced_exe.exists()}")

        if produced_exe.exists():
            dest_file = target_dist / "ResourceDownloader.exe"
            print(f"[COPY] 强行将产物复制至真实项目目录: {dest_file}")
            
            # 使用 shutil 二进制流写入
            with open(produced_exe, "rb") as f_src:
                with open(dest_file, "wb") as f_dst:
                    shutil.copyfileobj(f_src, f_dst)
            
            size_mb = dest_file.stat().st_size / (1024 * 1024)
            print("\n==================================================")
            print("SUCCESS: 打包并复制完成！")
            print(f"-> 目标路径: {dest_file}")
            print(f"-> 校验存在: {dest_file.exists()}")
            print(f"-> 文件体积: {size_mb:.2f} MB")
            print("==================================================")
        else:
            print("[ERR] PyInstaller 未能生成 EXE 文件")

    except Exception as e:
        print(f"[ERR] 打包异常: {e}")
    finally:
        # 清理临时构建目录
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    run_build()
