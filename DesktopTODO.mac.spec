# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from version import __version__

ROOT = Path(SPECPATH)
ICON = ROOT / "resources" / "icons" / "app.icns"

a = Analysis(
    ["main.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[(str(ROOT / "resources"), "resources")],
    hiddenimports=[
        "PySide6.QtNetwork",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PySide6.QtWebEngine",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.Qt3DCore",
        "PySide6.Qt3DRender",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.QtQuick",
        "PySide6.QtQml",
        "PySide6.QtPdf",
        "PySide6.QtBluetooth",
        "PySide6.QtNfc",
        "PySide6.QtPositioning",
        "PySide6.QtLocation",
        "PySide6.QtSensors",
        "PySide6.QtSerialPort",
        "PySide6.QtTextToSpeech",
        "PySide6.QtRemoteObjects",
        "matplotlib",
        "numpy",
        "pandas",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DesktopTODO",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="arm64",
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON) if ICON.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="DesktopTODO",
)

app = BUNDLE(
    coll,
    name="DesktopTODO.app",
    icon=str(ICON) if ICON.exists() else None,
    bundle_identifier="com.504615302.DesktopToDo",
    info_plist={
        "CFBundleName": "DesktopToDo",
        "CFBundleDisplayName": "桌面代办",
        "CFBundleShortVersionString": __version__,
        "CFBundleVersion": __version__,
        "CFBundlePackageType": "APPL",
        "CFBundleExecutable": "DesktopTODO",
        "CFBundleIconFile": "app.icns",
        "LSMinimumSystemVersion": "12.0",
        "NSHighResolutionCapable": True,
    },
    codesign_identity=None,
    entitlements_file=None,
)
