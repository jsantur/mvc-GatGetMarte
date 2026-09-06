# main.py (versión ULTRA-OPTIMIZADA - Inicio en Pantalla Completa)
import tkinter as tk
from tkinter import messagebox
from controller import OptimizedController
from model import OptimizedModel
from cache import OptimizedCacheManager, CacheConfig
from view import View
import ctypes
import sys
import os
import shutil
import atexit
import threading
import time
from pathlib import Path
import logging
from datetime import datetime
from notificacion import iniciar_sistema_notificaciones

# Configurar logging mejorado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('aplicacion.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AppManager:
    """Gestor principal de la aplicación con funcionalidades avanzadas."""
    
    def __init__(self):
        self.app_name = "SerenazgoControlApp"
        self.mutex = None
        self.cache_manager = None
        self.model = None
        self.view = None
        self.controller = None
        self.root = None
        self._cleanup_registered = False
        
    def singleton_check(self):
        """Asegura que solo una instancia de la aplicación se esté ejecutando."""
        try:
            mutex_name = f"Global\\{self.app_name}"
            self.mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
            
            if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
                tk.messagebox.showwarning(
                    "⚠️ Aplicación en Ejecución",
                    "La aplicación ya se encuentra ejecutándose.\n\n"
                    "Solo se permite una instancia a la vez."
                )
                return False
            
            logger.info("✅ Verificación de instancia única completada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en verificación de singleton: {e}")
            # Continuar si hay error en la verificación
            return True

    def get_base_path(self):
        """Obtiene la ruta base correcta tanto en desarrollo como en ejecutable."""
        if getattr(sys, 'frozen', False):
            # Si estamos en un ejecutable PyInstaller
            base_path = os.path.dirname(sys.executable)
            logger.info(f"📦 Ejecutándose desde ejecutable: {base_path}")
        else:
            # Intentar usar __file__ si está definida, de lo contrario usar sys.argv[0]
            try:
                base_path = os.path.dirname(os.path.abspath(__file__))
                logger.info(f"🔧 Ejecutándose en modo desarrollo con __file__: {base_path}")
            except NameError:
                base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
                logger.info(f"🔧 Ejecutándose sin __file__, usando sys.argv[0]: {base_path}")
        
        return base_path

    def setup_directories(self):
        """Crea las carpetas necesarias para la aplicación."""
        try:
            directories = [
                "REPORT",
                "IMG", 
                "cache",
                "data_json",
                "logs"
            ]
            
            for directory in directories:
                Path(directory).mkdir(exist_ok=True)
                
            logger.info("📁 Directorios de trabajo creados/verificados")
            
        except Exception as e:
            logger.error(f"❌ Error creando directorios: {e}")

    def setup_logo(self):
        """Copia el archivo de logo a la carpeta 'REPORT' si no existe."""
        try:
            logo_destino_folder = "REPORT"
            logo_destino_path = os.path.join(logo_destino_folder, "serenazgo_logo.png")

            if os.path.exists(logo_destino_path):
                logger.info("🖼️ Logo ya existe en la carpeta REPORT")
                return

            # Ubicaciones posibles del logo
            posibles_rutas_origen = [
                "D:/data/REPORT/serenazgo_logo.png",
                os.path.join(self.get_base_path(), "resources", "serenazgo_logo.png"),
                os.path.join(self.get_base_path(), "assets", "serenazgo_logo.png"),
                "serenazgo_logo.png",  # En el directorio actual
            ]

            logo_copiado = False
            for ruta_origen in posibles_rutas_origen:
                if os.path.exists(ruta_origen):
                    try:
                        shutil.copy2(ruta_origen, logo_destino_path)
                        logger.info(f"🖼️ Logo copiado de {ruta_origen} a {logo_destino_path}")
                        logo_copiado = True
                        break
                    except Exception as e:
                        logger.warning(f"⚠️ No se pudo copiar el logo desde {ruta_origen}: {e}")

            if not logo_copiado:
                logger.warning("⚠️ No se encontró el logo 'serenazgo_logo.png' en las ubicaciones esperadas")
                self._create_placeholder_logo(logo_destino_path)

        except Exception as e:
            logger.error(f"❌ Error configurando logo: {e}")

    def _create_placeholder_logo(self, logo_path):
        """Crea un logo placeholder si no se encuentra el original."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Crear imagen placeholder
            img = Image.new('RGB', (200, 100), color='#2c3e50')
            draw = ImageDraw.Draw(img)
            
            # Agregar texto
            text = "SERENAZGO"
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # Calcular posición centrada
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (200 - text_width) // 2
            y = (100 - text_height) // 2
            
            draw.text((x, y), text, fill='white', font=font)
            
            # Guardar imagen
            img.save(logo_path, 'PNG')
            logger.info(f"🖼️ Logo placeholder creado: {logo_path}")
            
        except Exception as e:
            logger.warning(f"⚠️ No se pudo crear logo placeholder: {e}")

    def configure_window(self, root):
        """Configura la ventana principal con optimizaciones."""
        try:
            # CONFIGURACIÓN PANTALLA COMPLETA AUTOMÁTICA
            root.state('zoomed')  # Windows: Maximizar ventana
            root.attributes('-topmost', True)  # Mantener al frente inicialmente
            
            # Configuraciones adicionales de ventana
            root.configure(bg="#f8f9fa")
            root.resizable(True, True)  # Permitir redimensionamiento
            
            # Centrar en pantalla si no es pantalla completa
            self._center_window_fallback(root)
            
            # Configurar icon si existe
            self._set_window_icon(root)
            
            logger.info("🖥️ Ventana configurada en pantalla completa")
            
        except Exception as e:
            logger.error(f"❌ Error configurando ventana: {e}")
            # Fallback a configuración básica
            root.geometry("1200x700")
            self._center_window_fallback(root)

    def _center_window_fallback(self, root):
        """Centra la ventana como fallback si falla la pantalla completa."""
        try:
            root.update_idletasks()
            
            # Obtener dimensiones
            ancho_ventana = root.winfo_width()
            alto_ventana = root.winfo_height()
            ancho_pantalla = root.winfo_screenwidth()
            alto_pantalla = root.winfo_screenheight()
            
            # Calcular posición centrada
            x = (ancho_pantalla // 2) - (ancho_ventana // 2)
            y = (alto_pantalla // 2) - (alto_ventana // 2)
            
            root.geometry(f'+{x}+{y}')
            
        except Exception as e:
            logger.warning(f"⚠️ Error centrando ventana: {e}")

    def _set_window_icon(self, root):
        """Establece el ícono de la ventana si está disponible."""
        try:
            icon_paths = [
                "serenazgo_icon.ico",
                os.path.join("resources", "serenazgo_icon.ico"),
                os.path.join("assets", "serenazgo_icon.ico")
            ]
            
            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    root.iconbitmap(icon_path)
                    logger.info(f"🎨 Ícono establecido: {icon_path}")
                    break
                    
        except Exception as e:
            logger.warning(f"⚠️ No se pudo establecer ícono: {e}")

    def initialize_cache(self):
        """Inicializa el sistema de caché optimizado."""
        try:
            # Configuración optimizada para la aplicación
            cache_config = CacheConfig(
                max_memory_size=2000,      # Más elementos en memoria
                max_memory_mb=400,         # Más memoria disponible
                max_disk_mb=2000,          # Más espacio en disco
                compression_threshold=512,  # Comprimir archivos más pequeños
                cleanup_interval=900,       # Limpieza cada 15 minutos
                max_threads=6,             # Más threads para mejor rendimiento
                enable_compression=True,
                enable_metrics=True
            )
            
            self.cache_manager = OptimizedCacheManager("app_cache", cache_config)
            logger.info("💾 Sistema de caché inicializado con configuración optimizada")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando caché: {e}")
            # Crear caché básico como fallback
            try:
                self.cache_manager = OptimizedCacheManager("app_cache")
                logger.info("💾 Caché básico inicializado como fallback")
                return True
            except Exception as e2:
                logger.error(f"❌ Error crítico con caché: {e2}")
                return False

    def initialize_components(self):
        """Inicializa los componentes principales de la aplicación."""
        try:
            # Crear ventana principal
            self.root = tk.Tk()
            self.configure_window(self.root)
            
            # Inicializar componentes en orden
            logger.info("🏗️ Inicializando componentes...")
            
            # Modelo con caché optimizado
            self.model = OptimizedModel(self.cache_manager)
            logger.info("📊 Modelo inicializado")
            
            # Vista con nueva interfaz optimizada
            self.view = View(self.root)
            logger.info("🖥️ Vista inicializada")
            
            # Controlador optimizado
            self.controller = OptimizedController(self.model, self.view)
            logger.info("🎮 Controlador inicializado")
            
            # Conectar vista con controlador
            self.view.set_controller(self.controller)
            logger.info("🔗 Componentes conectados")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando componentes: {e}")
            return False

    def delayed_initialization(self):
        """Realiza inicialización retardada de algunos componentes."""
        try:
            def init_delayed():
                # Actualizar turno y hora
                self.controller._actualizar_turno_logic()
                self.controller.aplicar_filtro("TODAS")
                self.controller.actualizar_contadores()
                self.controller.actualizar_reloj()
                
                # Quitar el topmost después de la inicialización
                self.root.after(2000, lambda: self.root.attributes('-topmost', False))
                
                logger.info("⏰ Inicialización retardada completada")

            # Programar inicialización después de 100ms
            self.root.after(100, init_delayed)
            
        except Exception as e:
            logger.error(f"❌ Error en inicialización retardada: {e}")

    def setup_cleanup(self):
        """Configura la limpieza automática al cerrar la aplicación."""
        if self._cleanup_registered:
            return
            
        def cleanup_on_exit():
            try:
                logger.info("🧹 Iniciando limpieza al cerrar...")
                self.cleanup_temp_files()
                
                # Cerrar componentes ordenadamente
                if self.controller:
                    self.controller._cleanup_resources()
                
                if self.model:
                    # Guardar configuración y cerrar caché sin vaciar Excel
                    self.model.shutdown()
                
                if self.cache_manager:
                    self.cache_manager.shutdown()
                
                logger.info("✅ Limpieza completada exitosamente")
                
            except Exception as e:
                logger.error(f"❌ Error en limpieza: {e}")

        atexit.register(cleanup_on_exit)
        self._cleanup_registered = True
        logger.info("🧹 Sistema de limpieza automática registrado")

    def cleanup_temp_files(self):
        """Limpia archivos temporales al cerrar la aplicación."""
        try:
            base_path = self.get_base_path()
            
            # Carpetas a limpiar (preservando archivos importantes)
            folders_to_clean = {
                "REPORT": ["serenazgo_logo.png"],  # Preservar solo el logo
                "IMG": []  # Eliminar todo
            }
            
            for folder, preserve_files in folders_to_clean.items():
                folder_path = os.path.join(base_path, folder)
                if os.path.exists(folder_path):
                    for filename in os.listdir(folder_path):
                        if filename not in preserve_files:
                            file_path = os.path.join(folder_path, filename)
                            try:
                                if os.path.isfile(file_path):
                                    os.remove(file_path)
                                elif os.path.isdir(file_path):
                                    shutil.rmtree(file_path)
                            except Exception as e:
                                logger.warning(f"⚠️ No se pudo eliminar {file_path}: {e}")
            
            logger.info("🧹 Archivos temporales limpiados")
            
        except Exception as e:
            logger.error(f"❌ Error limpiando archivos temporales: {e}")

    def handle_error(self, error_msg, exception=None):
        """Maneja errores de forma centralizada."""
        logger.error(f"❌ {error_msg}")
        if exception:
            logger.error(f"   Detalles: {exception}")
        
        try:
            tk.messagebox.showerror(
                "❌ Error de Aplicación",
                f"{error_msg}\n\nRevise el archivo de log para más detalles."
            )
        except:
            print(f"ERROR CRÍTICO: {error_msg}")

    def run(self):
        """Ejecuta la aplicación principal con manejo robusto de errores."""
        try:
            logger.info("🚀 Iniciando Sistema de Monitoreo SERENAZGO v2.0")
            
            # Verificar instancia única
            if not self.singleton_check():
                sys.exit(1)
            
            # Configuración inicial
            self.setup_directories()
            self.setup_logo()
            
            # Verificar archivo Excel
            self.ensure_excel_persistence()
            
            # Inicializar caché
            if not self.initialize_cache():
                self.handle_error("No se pudo inicializar el sistema de caché")
                sys.exit(1)
            
            # Configurar limpieza automática
            self.setup_cleanup()
            
            # Inicializar componentes principales
            if not self.initialize_components():
                self.handle_error("No se pudieron inicializar los componentes principales")
                sys.exit(1)
            
            # Iniciar sistema de notificaciones, pasando la vista principal
            iniciar_sistema_notificaciones(view=self.view)
            
            # Inicialización retardada
            self.delayed_initialization()
            
            logger.info("✅ Aplicación iniciada exitosamente")
            logger.info("🖥️ Interfaz en pantalla completa disponible")
            logger.info("⌨️ Presione F1 para ver atajos de teclado")
            
            # Ejecutar loop principal
            self.root.mainloop()
            
        except KeyboardInterrupt:
            logger.info("⏹️ Aplicación interrumpida por el usuario")
        except Exception as e:
            self.handle_error("Error crítico en la aplicación principal", e)
            sys.exit(1)
        finally:
            logger.info("🔚 Cerrando Sistema de Monitoreo SERENAZGO")

    def ensure_excel_persistence(self):
        """Asegura que el archivo Excel sea visible y persistente."""
        try:
            excel_file = os.path.join(self.get_base_path(), "unidades_registro.xlsx")
            
            logger.info(f"📊 Verificando archivo Excel: {excel_file}")
            
            # Verificar si el archivo existe
            if os.path.exists(excel_file):
                logger.info("✅ Archivo Excel encontrado")
                
                # Verificar permisos de escritura
                if os.access(excel_file, os.W_OK):
                    logger.info("✅ Archivo Excel tiene permisos de escritura")
                else:
                    logger.warning("⚠️ Archivo Excel no tiene permisos de escritura")
                    
                # Mostrar información del archivo
                file_size = os.path.getsize(excel_file)
                file_time = datetime.fromtimestamp(os.path.getmtime(excel_file))
                logger.info(f"📏 Tamaño: {file_size} bytes")
                logger.info(f"🕰️ Última modificación: {file_time}")
                
            else:
                logger.warning(f"⚠️ Archivo Excel no encontrado: {excel_file}")
                
                # Intentar crear el archivo si no existe
                logger.info("🔄 Creando archivo Excel...")
                self._create_excel_file()
                
        except Exception as e:
            logger.error(f"❌ Error verificando archivo Excel: {e}")

    def _create_excel_file(self):
        """Crea el archivo Excel con la estructura correcta, incluyendo la columna de observaciones."""
        try:
            excel_file = os.path.join(self.get_base_path(), "unidades_registro.xlsx")
            import pandas as pd
            df = pd.DataFrame()
            # Agregar todas las columnas, incluyendo observaciones
            df["FECHA"] = []
            df["HORA"] = []
            df["UNIDAD"] = []
            df["KM"] = []
            df["AP"] = []
            df["PO"] = []
            df["TURNO"] = []
            df["JURISDICCION"] = []
            df["OBSERVACIONES"] = []
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Registro de Unidades')
                workbook = writer.book
                worksheet = writer.sheets['Registro de Unidades']
                from openpyxl.styles import Font, Alignment, PatternFill
                header_font = Font(bold=True, color="FFFFFF")
                header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                for col in range(1, 10):  # 9 columnas
                    cell = worksheet.cell(row=1, column=col)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal="center")
            logger.info(f"✅ Archivo Excel creado exitosamente: {excel_file}")
            # Verificar integridad tras crear
            self._verify_excel_integrity(excel_file)
        except Exception as e:
            logger.error(f"❌ Error creando archivo Excel: {e}")

    def _verify_excel_integrity(self, excel_file):
        """Verifica que el archivo Excel tenga las columnas correctas."""
        try:
            import pandas as pd
            required_columns = [
                'FECHA', 'HORA', 'UNIDAD', 'KM', 'AP', 'PO', 'TURNO', 'JURISDICCION', 'OBSERVACIONES'
            ]
            if not os.path.exists(excel_file):
                logger.error(f"❌ El archivo Excel no existe tras crearlo: {excel_file}")
                messagebox.showerror("Error Excel", f"No se pudo crear el archivo: {excel_file}")
                return False
            df = pd.read_excel(excel_file, engine='openpyxl')
            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                logger.error(f"❌ Faltan columnas en el archivo Excel: {missing}")
                messagebox.showerror("Error Excel", f"Faltan columnas en el archivo Excel: {missing}")
                return False
            logger.info("✅ Archivo Excel verificado con todas las columnas correctas")
            return True
        except Exception as e:
            logger.error(f"❌ Error verificando integridad del archivo Excel: {e}")
            messagebox.showerror("Error Excel", f"Error verificando archivo Excel: {e}")
            return False

def main():
    """Función principal de entrada."""
    try:
        # Configurar codificación para Windows
        if sys.platform.startswith('win'):
            os.system('chcp 65001 > nul')  # UTF-8
        
        # Crear y ejecutar aplicación
        app = AppManager()
        app.run()
        
    except Exception as e:
        logger.error(f"❌ Error fatal en main: {e}")
        try:
            tk.messagebox.showerror(
                "❌ Error Fatal",
                f"No se pudo iniciar la aplicación:\n{str(e)}\n\nContacte al administrador del sistema."
            )
        except:
            print(f"ERROR FATAL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
