# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = [('REPORT/serenazgo_logo.png', 'REPORT'), ('help/Main.png', 'help'), ('help/Megafonos.png', 'help'), ('help/Ocurrencias.png', 'help'), ('help/Unidades.png', 'help'), ('megafonos.py', '.'), ('report_ocurrencias.py', '.'), ('report_unidades.py', '.'), ('gestion_unidades.py', '.'), ('unidades.txt', '.'), ('unidades.txt.backup', '.'), ('unidades_registro.xlsx', '.'), ('gemini_config.json', '.'), ('config.json', '.'), ('config_db.json', '.'), ('constants.py', '.'), ('cache.py', '.'), ('notificacion.py', '.'), ('distribucion.py', '.'), ('download_dicts.py', '.'), ('img', 'img'), ('utils.py', '.'), ('notificacion_config.json', '.'), ('notificacion_system.log', '.'), ('help/Presentacion.jpeg', 'help')]
binaries = []
hiddenimports = ['tkinter', 'tkinter.messagebox', '_tkinter', 'pytz', 'mysql.connector', 'google.generativeai', 'winsound', 'ntplib', 'pyperclip', 'psutil', 'PIL', 'openpyxl', 'pandas', 'plyer']
datas += collect_data_files('tkinter')
hiddenimports += collect_submodules('tkinter')
tmp_ret = collect_all('google.generativeai')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('spellchecker')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('PIL')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('openpyxl')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pandas')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('plyer')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
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
    name='SerenazgoMonitor',
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
    icon=['logo.ico'],
)
