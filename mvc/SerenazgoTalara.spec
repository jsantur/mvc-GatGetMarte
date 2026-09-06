# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_data_files
import sys
import os

# Configuración de datos a incluir
datas = [
    ('help', 'help'),                          # Imágenes de ayuda
    ('config.json', '.'),                      # Configuración general
    ('gemini_config.json', '.'),               # API key Gemini
    ('unidades.txt', '.'),                     # Datos de unidades
    ('logo.ico', '.'),                         # Ícono
    ('REPORT/serenazgo_logo.png', 'REPORT'),   # Logo reportes
    ('unidades_registro.xlsx', '.'),          # Excel base (si existe)
]

# Solo incluir archivos si existen
for src, dst in [('unidades_registro.xlsx', '.')]:
    if os.path.exists(src):
        datas.append((src, dst))

binaries = []

# Hidden imports - módulos locales y librerías
hiddenimports = [
    # SSL y red
    'certifi',
    'requests',
    'urllib3',
    'ssl',
    
    # Módulos locales del proyecto
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
    'wialon_api',
    'gestion_unidades',
    'megafonos',
    
    # Librerías de terceros
    'pandas',
    'pandas._libs.tslibs.base',
    'pandas._libs.tslibs.timedeltas',
    'pandas._libs.tslibs.timestamps',
    'pandas._libs.tslibs.timezones',
    'pandas._libs.tslibs.conversion',
    'openpyxl',
    'openpyxl.cell',
    'openpyxl.styles',
    'openpyxl.utils',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'pyperclip',
    'google.generativeai',
    'google.generativeai.types',
    'spellchecker',
    'sqlite3',
    'dateutil',
    'dateutil.parser',
    'dateutil.tz',
    'pytz',
    'pytz.tzinfo',
    'platform',
    'threading',
    'queue',
    'tkinter',
    'tkinter.ttk',
    'tkinter.scrolledtext',
    'tkinter.messagebox',
]

# Collect all para requests (incluye certificados SSL)
tmp_ret = collect_all('requests')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Collect data files para pandas (archivos de zona horaria, etc.)
try:
    pandas_datas = collect_data_files('pandas')
    datas += pandas_datas
except:
    pass

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy.random._examples', 'scipy', 'tkinter.test', 
              'unittest', 'pydoc', 'pdb', 'doctest', 'language_tool_python'],  # Excluir LanguageTool (muy pesado)
    noarchive=False,
    optimize=1,  # Optimización básica
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # MODO DIRECTORY: archivos separados
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

# MODO DIRECTORY: Coleccionar todo en carpeta dist/SerenazgoTalara
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SerenazgoTalara'
)
