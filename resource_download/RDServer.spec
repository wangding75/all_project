# PyInstaller specification for the production standalone RD server.
# This file is intentionally separate from ResourceDownloader.spec: the
# desktop executable is a thin client, while this executable owns the server
# runtime shipped in a complete RD release package.

from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


ROOT_DIR = Path(SPECPATH).resolve()
SERVER_DIR = ROOT_DIR / "server"
CLIENT_UI_DIR = ROOT_DIR / "client" / "ui"

# Make the server package discoverable while PyInstaller evaluates hooks.
sys.path.insert(0, str(SERVER_DIR))

app_modules = [item for item in collect_submodules("app") if not item.endswith(".mock_node")]
platform_modules = collect_submodules("platforms")

hiddenimports = sorted(
    set(
        app_modules
        + platform_modules
        + [
            "app.main",
            "app.api",
            "app.api.router",
            "app.api.admin",
            "app.api.auth_router",
            "app.config",
            "app.db",
            "app.jobs",
            "app.license_gateway",
            "app.security_boot",
            "platforms.registry",
            "platforms.device_discovery",
            "platforms.readiness",
            "platforms.runtime",
        ]
    )
)

datas = []
for package_name in ("app", "platforms"):
    datas.extend(collect_data_files(package_name, include_py_files=False))

if CLIENT_UI_DIR.is_dir():
    datas.append((str(CLIENT_UI_DIR), "ui"))

# Fanqie signs through a JavaScript asset loaded at runtime.  Keep it in the
# same relative location used by the source runtime.
fanqie_oracle = SERVER_DIR / "platforms" / "fanqie" / "oracle_sign.js"
if fanqie_oracle.is_file():
    datas.append((str(fanqie_oracle), "platforms/fanqie"))


a = Analysis(
    [str(ROOT_DIR / "scripts" / "rd_server_entry.py")],
    pathex=[str(SERVER_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "tests", "IPython", "tkinter"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="RDServer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)
