# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

root_dir = Path(SPECPATH).resolve()
datas = [(str(root_dir / 'client' / 'ui'), 'ui')]
binaries = []
hiddenimports = [
    'anyio._backends._asyncio',
    'license_service_client.device',
    'license_service_client.signing',
    'cryptography.hazmat.primitives.asymmetric.ed25519',
]
tmp_ret = collect_all('webview')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    [str(root_dir / 'client' / 'desktop' / 'main.py')],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'IPython', 'pytest', 'unittest', 'ruff', 'app', 'platforms', 'uvicorn', 'fastapi', 'sqlalchemy'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ResourceDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
