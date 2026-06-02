# -*- mode: python ; coding: utf-8 -*-

"""PyInstaller spec file for PyCaffeine."""

import sys
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent
ASSETS = ROOT / "assets"
VERSION_RC = ROOT / "spec" / "version.rc"

IS_LINUX = sys.platform.startswith("linux")

# .ico for Windows exe icon, SVG bundled for tray icon at runtime
icon_file = ASSETS / "pycaffeine-icon.ico"
icon_path = str(icon_file) if icon_file.exists() else None

a = Analysis(
    [str(ROOT / "pycaffeine" / "__main__.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ASSETS / "pycaffeine-icon.svg"), "assets"),
        (str(ASSETS / "pycaffeine-icon-off.svg"), "assets"),
    ],
    hiddenimports=["PyQt6.QtDBus"] if IS_LINUX else [],
    hookspath=[],
    runtime_hooks=[],
    # mouseinfo/tkinter must be excluded: the bundled _tkinter is broken
    # (Tcl symbol mismatch), and mouseinfo calls sys.exit() when tkinter fails
    # to import, killing the app from the worker thread. Without mouseinfo
    # bundled, pyautogui catches the ImportError and degrades gracefully
    # (mouse movement only needs Xlib).
    excludes=["tkinter", "_tkinter", "mouseinfo"] + ([] if IS_LINUX else ["PyQt6.QtDBus"]),
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="pycaffeine",
    debug=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,
    icon=icon_path,
    version=str(VERSION_RC),
    uac_admin=False,
)
