# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('REPORT/serenazgo_logo.png', 'REPORT'), ('megafonos.txt', '.'), ('porce.ico', '.'), ('cache.py', '.'), ('megafonos.py', '.')],
    hiddenimports=['mysql.connector', 'pytz', 'win32clipboard', 'win32con', 'win32gui', 'win32ui'],
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
    name='ControlUnidadesApp',
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
    icon=['porce.ico'],
)
