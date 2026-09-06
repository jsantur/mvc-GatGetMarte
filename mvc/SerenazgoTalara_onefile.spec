# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [
    ('help', 'help'),
    ('REPORT', 'REPORT'),
    ('IMG', 'IMG'),
    ('config.json', '.'),
    ('config_db.json', '.'),
    ('gemini_config.json', '.'),
    ('notificacion_config.json', '.'),
    ('unidades.txt', '.'),
    ('unidades_registro.xlsx', '.'),
    ('bd_serenos.json', '.'),
    ('logo.ico', '.')
]

binaries = []

hiddenimports = [
    'certifi',
    'pytz',
    'mysql.connector',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'openpyxl',
    'pandas',
    'plyer',
    'winsound',
    'ntplib',
    'pyperclip',
    'psutil',
    'google.generativeai',
    'tkinter',
    'tkinter.messagebox',
    'webbrowser',
    'atexit',
    'ctypes',
    'threading',
    'time',
    'json',
    'os',
    'sys',
    'shutil',
    'pathlib',
    'logging',
    'datetime'
]

# Recopilar todo lo relacionado con requests, PIL, openpyxl, pandas
for module in ['requests', 'google.generativeai', 'PIL', 'openpyxl', 'pandas', 'certifi']:
    tmp_ret = collect_all(module)
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SerenazgoTalara',
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
    icon='logo.ico',
)
