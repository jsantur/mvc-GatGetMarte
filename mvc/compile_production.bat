@echo off
echo ===================================================
echo   COMPILANDO SERENAZGO TALARA - VERSION PRODUCCION
echo ===================================================
echo.

REM Limpiar carpetas previas
echo [1/4] Limpiando carpetas de compilacion previas...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Instalar/Actualizar dependencias criticas
echo [2/4] Verificando dependencias...
pip install pyinstaller pillow mysql-connector-python pyperclip ntplib pytz pandas openpyxl psutil google-generativeai requests certifi plyer winsound pywin32

REM Compilar usando el archivo .spec
echo [3/4] Iniciando PyInstaller con SerenazgoTalara_full.spec...
pyinstaller --clean SerenazgoTalara_full.spec

REM Verificar resultado
echo.
echo [4/4] Verificando resultado...
if exist "dist\SerenazgoTalara\SerenazgoTalara.exe" (
    echo.
    echo ===================================================
    echo   ¡COMPILACION EXITOSA!
    echo   Ubicacion: dist\SerenazgoTalara\SerenazgoTalara.exe
    echo ===================================================
) else (
    echo.
    echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    echo   ERROR: No se encontro el ejecutable generado.
    echo   Revise la salida anterior para ver los errores.
    echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
)

pause
