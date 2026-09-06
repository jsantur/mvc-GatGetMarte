@echo off
REM Script mejorado para compilar ControlUnidadesApp con soporte para base de datos

REM 1. Instalar dependencias necesarias
pip install pyinstaller pillow mysql-connector-python pyperclip ntplib pytz

REM 2. Crear estructura de directorios necesaria
if not exist "REPORT" mkdir REPORT
if not exist "IMG" mkdir IMG
if not exist "cache" mkdir cache

REM 3. Convertir el logo PNG a formato ICO (requiere Pillow)
if exist "REPORT\serenazgo_logo.png" (
    python -c "from PIL import Image; img = Image.open('REPORT/serenazgo_logo.png'); img.save('porce.ico', format='ICO', sizes=[(32,32), (48,48), (64,64), (128,128), (256,256)])"
) else (
    echo El archivo REPORT/serenazgo_logo.png no existe, se omitirá la creación del ícono
)

REM 4. Crear el archivo de configuración de la base de datos si no existe
if not exist "config_db.json" (
    echo Creando archivo de configuración de la base de datos...
    echo { "host": "localhost", "database": "serenazgo_db", "user": "root", "password": "", "port": "3306" } > config_db.json
)

REM 5. Crear el archivo ejecutable con PyInstaller
pyinstaller --onefile --windowed ^
    --icon=porce.ico ^
    --add-data "REPORT/serenazgo_logo.png;REPORT" ^
    --add-data "porce.ico;." ^
    --add-data "config_db.json;." ^
    --name "ControlUnidadesApp" ^
    --hidden-import mysql.connector ^
    --hidden-import pytz ^
    --hidden-import ntplib ^
    --hidden-import pyperclip ^
    main.py

REM 6. Copiar archivos necesarios al directorio dist
xcopy /Y /I "config_db.json" "dist\"
xcopy /Y /I /S "IMG" "dist\IMG\"
xcopy /Y /I /S "cache" "dist\cache\"

REM 7. Mensaje final con instrucciones
echo.
echo ¡Ejecutable creado con éxito!
echo.
echo El archivo se encuentra en: dist\ControlUnidadesApp.exe
echo.
echo INSTRUCCIONES IMPORTANTES:
echo 1. Asegúrese de tener MySQL instalado y configurado
echo 2. Cree la base de datos "serenazgo_db" si no existe
echo 3. Ejecute el programa como administrador si tiene problemas con permisos
echo 4. Si necesita cambiar la configuración de la base de datos, edite el archivo config_db.json
echo.
pause