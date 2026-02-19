# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAIN_SCRIPT = str(PROJECT_ROOT / "main.py")

hiddenimports = []
hiddenimports += collect_submodules("PyQt6")
hiddenimports += collect_submodules("cv2")
hiddenimports += ["mss", "pynput", "openpyxl", "xlrd"]

a = Analysis(
    [MAIN_SCRIPT],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AHKManipulator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AHKManipulator",
)
app = BUNDLE(
    coll,
    name="AHKManipulator.app",
    icon=None,
    bundle_identifier="com.ahkmanipulator.app",
)
