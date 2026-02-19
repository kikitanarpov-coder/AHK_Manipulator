# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

spec_path = Path(globals().get("__file__", globals().get("SPEC", "build/windows.spec"))).resolve()
PROJECT_ROOT = spec_path.parent.parent
MAIN_SCRIPT = str(PROJECT_ROOT / "main.py")

hiddenimports = [
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "cv2",
    "numpy",
    "mss",
    "pynput",
    "openpyxl",
    "xlrd",
]
datas = [
    (str(PROJECT_ROOT / "ui" / "recording_listener_worker.py"), "ui"),
]

a = Analysis(
    [MAIN_SCRIPT],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
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
    a.binaries,
    a.datas,
    [],
    name="AHKManipulator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
