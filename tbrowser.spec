# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller derleme tanımı — tbrowser v1.0.0.

Kullanım:  pyinstaller tbrowser.spec --noconfirm
Çıktı:     dist/tbrowser/ (klasör) — dağıtımda zip'lenir.
"""

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all("PyQt6")

a = Analysis(
    ["tbrowser.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="tbrowser",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
    upx=False,
    upx_exclude=[],
    name="tbrowser",
)
