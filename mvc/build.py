import json
import os
import sys
import PyInstaller.__main__
from shutil import copy, rmtree
from pathlib import Path

# --- Configuración ---
APP_NAME = "SerenazgoMonitor"
VERSION = "1.0"
ICON_FILE = "logo.ico"  # Asegúrate de que este archivo exista

# Archivos a incluir en el ejecutable
BUNDLED_DATA_FILES = [
    ("REPORT/serenazgo_logo.png", "REPORT"),
    ("help/Main.png", "help"),  # Imagen principal
    ("help/Megafonos.png", "help"),  # Imagen de megáfonos
    ("help/Ocurrencias.png", "help"),  # Imagen de ocurrencias
    ("help/Unidades.png", "help"),  # Imagen de unidades
    ("megafonos.py", "."),
    ("report_ocurrencias.py", "."),
    ("report_unidades.py", "."),
    ("gestion_unidades.py", "."),
    ("unidades.txt", "."),
    ("unidades.txt.backup", "."),
    ("unidades_registro.xlsx", "."),
    ("gemini_config.json", "."),
    ("config.json", "."),
    ("config_db.json", "."),
    ("constants.py", "."),
    ("cache.py", "."),
    ("notificacion.py", "."),
    ("distribucion.py", "."),
    ("download_dicts.py", "."),
    ("img", "img"),  # Carpeta de imágenes
    ("utils.py", "."),  # <--- Añadido para notificaciones
    ("notificacion_config.json", "."),  # <--- Añadido para notificaciones
    ("notificacion_system.log", "."),  # <--- Añadido para notificaciones
    ("arial.ttf", "."),  # Fuente para reportes JPG si existe
    ("help/Presentacion.jpeg", "help")  # <-- Añadido para Contacto
]

def prepare_environment():
    """Prepara el entorno eliminando builds previos y creando directorios."""
    print("Preparando entorno de compilación...")
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            print(f"Eliminando directorio antiguo '{folder}'...")
            rmtree(folder)
    os.makedirs('REPORT', exist_ok=True)
    os.makedirs('IMG', exist_ok=True)
    verify_required_files()

def verify_required_files():
    """Verifica y crea/copia archivos requeridos si es necesario."""
    if not os.path.exists(ICON_FILE):
        print(f"Error: Archivo de ícono '{ICON_FILE}' no encontrado.")
        sys.exit(1)
    for src, _ in BUNDLED_DATA_FILES:
        if not os.path.exists(src):
            if src == "REPORT/serenazgo_logo.png":
                copy_logo_from_alternate_locations()
            elif src == "unidades.txt":
                print(f"Creando '{src}' vacío con datos por defecto...")
                with open(src, "w", encoding="utf-8") as f:
                    f.write("# Formato: Alias;Código;Tipo\nH1 / EUI-621;EUI-621;PICKUP\n")
            elif src == "gemini_config.json":
                print(f"Creando '{src}' con configuración por defecto...")
                with open(src, "w", encoding="utf-8") as f:
                    json.dump({"api_key": "TU_API_KEY_AQUÍ"}, f)
            elif src == "notificacion_config.json":
                print(f"Creando '{src}' con configuración por defecto de notificaciones...")
                with open(src, "w", encoding="utf-8") as f:
                    json.dump({
                        "notificacion_inicial_mostrada": False,
                        "ultimo_recordatorio": None,
                        "sms_enabled": False,
                        "sms_api_key": "",
                        "intervalo_minutos": 1
                    }, f, indent=2, ensure_ascii=False)
            elif src == "notificacion_system.log":
                print(f"Creando archivo de log vacío para notificaciones: '{src}'...")
                with open(src, "w", encoding="utf-8") as f:
                    f.write("")
            elif src == "arial.ttf":
                print(f"Advertencia: '{src}' no encontrado. Si usas reportes JPG, asegúrate de tener la fuente Arial disponible.")
            elif src == "utils.py":
                print(f"Error: '{src}' es requerido para las notificaciones. Asegúrate de que existe.")
                sys.exit(1)
            else:
                print(f"Advertencia: '{src}' no encontrado.")

def copy_logo_from_alternate_locations():
    """Intenta copiar el logo desde ubicaciones alternativas."""
    logo_dest = "REPORT/serenazgo_logo.png"
    possible_paths = [
        "D:/data/REPORT/serenazgo_logo.png",
        os.path.join(os.path.dirname(__file__), "resources", "serenazgo_logo.png"),
        os.path.join(os.path.dirname(__file__), "assets", "serenazgo_logo.png")
    ]
    for ruta in possible_paths:
        if os.path.exists(ruta):
            try:
                os.makedirs(os.path.dirname(logo_dest), exist_ok=True)
                copy(ruta, logo_dest)
                print(f"Logo copiado desde {ruta}")
                break
            except Exception as e:
                print(f"No se pudo copiar logo desde {ruta}: {e}")

def get_pyinstaller_data_args():
    """Genera la lista de argumentos --add-data para PyInstaller."""
    data_args = []
    for src, dest in BUNDLED_DATA_FILES:
        if os.path.exists(src):
            data_args.append(f"{src}{os.pathsep}{dest}")
        else:
            print(f"Advertencia: Archivo '{src}' no encontrado, omitiendo.")
    return data_args

def build_executable():
    """Compila el ejecutable con PyInstaller."""
    print("Iniciando compilación del ejecutable...")

    pyinstaller_options = [
        'main.py',
        '--onefile',
        '--windowed',
        '--clean',
        f'--name={APP_NAME}',
        f'--icon={ICON_FILE}',
        '--noconfirm',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.messagebox',
        '--hidden-import=_tkinter',
        '--hidden-import=pytz',
        '--hidden-import=mysql.connector',
        '--hidden-import=google.generativeai',
        '--hidden-import=winsound',
        '--hidden-import=ntplib',
        '--hidden-import=pyperclip',
        '--hidden-import=psutil',
        '--hidden-import=PIL',
        '--hidden-import=openpyxl',
        '--hidden-import=pandas',
        '--hidden-import=plyer',
        '--collect-all=google.generativeai',
        '--collect-all=spellchecker',
        '--collect-all=PIL',
        '--collect-all=openpyxl',
        '--collect-all=pandas',
        '--collect-all=plyer',
        '--collect-submodules=tkinter',
        '--collect-data=tkinter'
    ]

    for data_arg in get_pyinstaller_data_args():
        pyinstaller_options.append(f'--add-data={data_arg}')

    try:
        PyInstaller.__main__.run(pyinstaller_options)
        print("\n✅ Compilación completada exitosamente!")
        print(f"El ejecutable está en 'dist' como '{APP_NAME}.exe'")
        print("\nIMPORTANTE: Si las notificaciones no aparecen en Windows, asegúrate de tener plyer correctamente instalado y que tu antivirus no bloquee las notificaciones.")
    except Exception as e:
        print(f"\n❌ Error durante la compilación: {e}")
        print("Si el error está relacionado con plyer o notificaciones, revisa la documentación y asegúrate de que plyer esté en requirements.txt y correctamente instalado.")
        sys.exit(1)

def main():
    print(f"\n{'='*50}")
    print(f"COMPILANDO {APP_NAME} v{VERSION}")
    print(f"{'='*50}\n")
    prepare_environment()
    build_executable()
    print("\nProceso terminado.")

if __name__ == "__main__":
    main()