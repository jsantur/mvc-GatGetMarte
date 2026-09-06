# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [
    ('help', 'help'),
    ('REPORT', 'REPORT'),
    ('IMG', 'IMG'),
    ('BD SERENOS', 'BD SERENOS'),
    ('data_json', 'data_json'),
    ('reportes_json', 'reportes_json'),
    ('config.json', '.'),
    ('config_db.json', '.'),
    ('drive_api.json', '.'),
    ('drive_file_metadata.json', '.'),
    ('gemini_config.json', '.'),
    ('openai_config.json', '.'),
    ('notificacion_config.json', '.'),
    ('unidades.txt', '.'),
    ('unidades.json', '.'),
    ('unidades_registro.xlsx', '.'),
    ('bd_serenos.json', '.'),
    ('serenazgo_db.sqlite', '.'),
    ('logo.ico', '.'),
    ('porce.ico', '.'),
    ('proce.ico', '.'),
    ('manual_usuario.md', '.')
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
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.scrolledtext',
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
    'datetime',
    'win32gui',
    'win32ui',
    'win32con',
    'win32clipboard',
    'wialon_api',
    're',
    'unicodedata',
    'sqlite3',
    # Módulos del proyecto
    'model',
    'view',
    'controller',
    'utils',
    'units_manager',
    'cache',
    'constants',
    'modern_widgets',
    'notificacion',
    'excel_persistence',
    'report_unidades',
    'report_ocurrencias',
    'megafonos_dialog',
    'daily_report_dialog',
    'gestion_unidades',
    'megafonos'
]

# Recopilar todo lo relacionado con requests y google-generativeai
tmp_ret = collect_all('requests')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret2 = collect_all('google.generativeai')
datas += tmp_ret2[0]; binaries += tmp_ret2[1]; hiddenimports += tmp_ret2[2]

tmp_ret3 = collect_all('PIL')
datas += tmp_ret3[0]; binaries += tmp_ret3[1]; hiddenimports += tmp_ret3[2]

tmp_ret4 = collect_all('openpyxl')
datas += tmp_ret4[0]; binaries += tmp_ret4[1]; hiddenimports += tmp_ret4[2]



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
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [('W', None, 'OPTION')],
    exclude_binaries=True,
    name='SerenazgoTalara',
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
    icon='logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SerenazgoTalara',
)
