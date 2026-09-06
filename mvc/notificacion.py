# notificacion.py - Sistema de Notificaciones Independiente
import tkinter as tk
from tkinter import messagebox
import json
import os
import sys
import logging
from datetime import datetime, time
import pytz
from plyer import notification
import threading
import time as time_module
import importlib.util
from typing import Optional, Dict, List
from report_ocurrencias import ToastNotification
from utils import UI_CONSTANTS

class SistemaNotificaciones:
    """Sistema de notificaciones independiente para reportes de unidades."""
    
    def __init__(self, view=None):
        self.config_file = "notificacion_config.json"
        self.log_file = "notificacion_system.log"
        self.config = self._load_config()
        self.running = False
        self.notification_thread = None
        self.root = None
        self.ultima_notificacion = None
        self.view = view  # Referencia a la vista principal
        
        # Configurar logging
        self._setup_logging()
        
        # Definir turnos y horas válidas
        self.turnos = {
            "DÍA": {
                "horario": (time(6, 0), time(13, 59)),
                "horas_validas": [
                    time(8, 0), time(9, 0), time(10, 0), time(11, 0), time(12, 0)
                ]
            },
            "TARDE": {
                "horario": (time(14, 0), time(21, 59)),
                "horas_validas": [
                    time(16, 0), time(17, 0), time(18, 0), time(19, 0), time(20, 0)
                ]
            },
            "NOCHE": {
                "horario": (time(22, 0), time(5, 59)),
                "horas_validas": [
                    time(0, 0), time(0, 30), time(1, 0), time(1, 30), time(2, 0),
                    time(2, 30), time(3, 0), time(3, 30), time(4, 0), time(4, 30), time(5, 0)
                ]
            }
        }
        
        self.logger.info("Sistema de notificaciones inicializado")
    
    def _setup_logging(self):
        """Configura el sistema de logging."""
        self.logger = logging.getLogger('SistemaNotificaciones')
        self.logger.setLevel(logging.INFO)
        
        # Evitar duplicación de handlers
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_file, encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _load_config(self) -> Dict:
        """Carga la configuración desde el archivo JSON."""
        default_config = {
            "notificacion_inicial_mostrada": False,
            "ultimo_recordatorio": None,
            "sms_enabled": False,
            "sms_api_key": "",
            "intervalo_minutos": 1  # Por defecto, cada 1 minuto para pruebas
        }
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Si falta la clave, agregarla
                    if "intervalo_minutos" not in config:
                        config["intervalo_minutos"] = 1
                    return config
        except Exception as e:
            self.logger.error(f"Error al cargar configuración: {e}")
        return default_config
    
    def _save_config(self):
        """Guarda la configuración en el archivo JSON."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error al guardar configuración: {e}")
    
    def _get_hora_actual(self) -> datetime:
        """Obtiene la hora actual en la zona horaria de Lima."""
        lima_tz = pytz.timezone('America/Lima')
        return datetime.now(lima_tz)
    
    def _determinar_turno_actual(self) -> Optional[str]:
        """Determina el turno actual basado en la hora del sistema."""
        ahora = self._get_hora_actual()
        hora_actual = ahora.time()
        
        for turno, info in self.turnos.items():
            inicio, fin = info["horario"]
            
            if turno == "NOCHE":
                # Caso especial para turno noche que cruza medianoche
                if hora_actual >= inicio or hora_actual <= fin:
                    return turno
            else:
                if inicio <= hora_actual <= fin:
                    return turno
        
        return None
    
    def _es_hora_valida(self, hora_actual: time, turno: str) -> bool:
        if turno not in self.turnos:
            return False
        horas_validas = self.turnos[turno]["horas_validas"]
        # Comparar solo hora y minuto, ignorando segundos y microsegundos
        return any(hora_actual.hour == h.hour and hora_actual.minute == h.minute for h in horas_validas)
    
    def _mostrar_notificacion_inicial(self):
        """Muestra la notificación inicial al iniciar el programa usando Toast con botón de cerrar."""
        if self.config.get("notificacion_inicial_mostrada", False):
            return
        try:
            # Crear root oculto si no existe
            if self.root is None:
                self.root = tk.Tk()
                self.root.withdraw()
                self.root.attributes('-topmost', True)
            # Mostrar ToastNotification con botón de cerrar
            toast = ToastNotification(self.root, "¡DEBO PEDIR REPORTE!", title="🔔 Sistema de Reportes", duration=6000)
            self.logger.info("Notificación inicial mostrada (Toast)")
            # Marcar como mostrada
            self.config["notificacion_inicial_mostrada"] = True
            self._save_config()
        except Exception as e:
            self.logger.error(f"Error al mostrar notificación inicial (Toast): {e}")
    
    def _crear_root_oculto(self):
        """Crea una ventana raíz oculta para soportar messagebox."""
        if self.root is None:
            self.root = tk.Tk()
            self.root.withdraw()  # Ocultar la ventana
            self.root.attributes('-topmost', True)
    
    def _mostrar_messagebox_reporte(self) -> bool:
        """Muestra un popup centrado con botones SÍ y NO. Retorna True si el usuario selecciona SÍ."""
        try:
            self._crear_root_oculto()
            resultado = [False]  # Usar lista para mutabilidad en closure
            popup = tk.Toplevel(self.root)
            popup.title("Sistema de Reportes")
            popup.configure(bg='white')
            popup.overrideredirect(True)
            popup.attributes('-topmost', True)

            # Contenedor principal
            main_frame = tk.Frame(popup, bg='white', padx=40, pady=40)
            main_frame.pack()

            # Texto principal en azul oscuro
            label_principal = tk.Label(
                main_frame,
                text="¡ES EL MOMENTO DEL REPORTE!",
                font=("Segoe UI", 20, "bold"),
                fg='#1e3a8a',  # Azul oscuro
                bg='white',
                justify='center'
            )
            label_principal.pack(pady=(0, 10))

            # Texto secundario en azul oscuro
            label_secundario = tk.Label(
                main_frame,
                text="¿QUIERES TOMARLO?",
                font=("Segoe UI", 20, "bold"),
                fg='#1e3a8a',  # Azul oscuro
                bg='white',
                justify='center'
            )
            label_secundario.pack(pady=(0, 30))

            # Botones
            button_frame = tk.Frame(main_frame, bg='white')
            button_frame.pack()
            
            def on_si():
                self.logger.info("Usuario seleccionó SÍ en la notificación")
                resultado[0] = True
                popup.destroy()
            def on_no():
                self.logger.info("Usuario seleccionó NO en la notificación")
                resultado[0] = False
                popup.destroy()
            
            # Botón SÍ (verde)
            btn_si = tk.Button(
                button_frame, 
                text="SÍ", 
                font=("Segoe UI", 16, "bold"), 
                fg='white',
                bg='#22c55e',  # Verde
                relief='flat', 
                borderwidth=0,
                command=on_si, 
                padx=40, 
                pady=12,
                cursor='hand2'
            )
            btn_si.pack(side=tk.LEFT, padx=10)
            
            # Botón NO (rojo)
            btn_no = tk.Button(
                button_frame, 
                text="NO", 
                font=("Segoe UI", 16, "bold"), 
                fg='white',
                bg='#ef4444',  # Rojo
                relief='flat', 
                borderwidth=0,
                command=on_no, 
                padx=40, 
                pady=12,
                cursor='hand2'
            )
            btn_no.pack(side=tk.LEFT, padx=10)

            # Centrar la ventana en pantalla
            popup.update_idletasks()
            screen_width = popup.winfo_screenwidth()
            screen_height = popup.winfo_screenheight()
            window_width = popup.winfo_width()
            window_height = popup.winfo_height()
            x = (screen_width // 2) - (window_width // 2)
            y = (screen_height // 2) - (window_height // 2)
            popup.geometry(f"+{x}+{y}")

            # Cierre automático tras 30 segundos
            def cerrar_automaticamente():
                self.logger.info("Notificación cerrada automáticamente tras 30 segundos")
                popup.destroy()
            
            popup.after(30000, cerrar_automaticamente)
            
            if self.root is None:
                self.root = tk.Tk()
                self.root.withdraw()
                self.root.attributes('-topmost', True)
            self.root.wait_window(popup)
            return resultado[0]
        except Exception as e:
            self.logger.error(f"Error al mostrar popup de reporte: {e}")
            return False
    
    def _activar_ventana_principal(self):
        """Abre el reporte de unidades usando la vista principal si está disponible."""
        try:
            if self.view and hasattr(self.view, 'abrir_reporte_unidades'):
                self.view.abrir_reporte_unidades()
                self.logger.info("Reporte de unidades abierto desde notificación (popup SÍ) usando la vista principal.")
                return True
            else:
                # Fallback: abrir como proceso externo
                import subprocess
                import sys
                subprocess.Popen([sys.executable, "report_unidades.py"])
                self.logger.info("report_unidades.py ejecutado desde notificación (popup SÍ) (fallback)")
                return True
        except Exception as e:
            self.logger.error(f"Error al abrir reporte de unidades: {e}")
            return False
    
    def _enviar_sms_opcional(self):
        """Envía SMS opcional si está configurado."""
        if not self.config.get("sms_enabled", False):
            return
        
        try:
            # Aquí se implementaría la lógica de SMS con Twilio u otra API
            # Por ahora solo se registra en el log
            self.logger.info("SMS opcional habilitado pero no implementado")
        except Exception as e:
            self.logger.error(f"Error al enviar SMS: {e}")
    
    def _procesar_notificacion_reporte(self):
        """Procesa la notificación de reporte cuando es hora válida."""
        turno_actual = self._determinar_turno_actual()
        hora_actual = self._get_hora_actual().time()
        print(f"DEBUG: Turno: {turno_actual}, Hora: {hora_actual}")  # Depuración
        if not turno_actual:
            return
        if not self._es_hora_valida(hora_actual, turno_actual):
            return
        # Evitar notificaciones duplicadas en el mismo minuto
        hora_str = hora_actual.strftime("%H:%M")
        if self.ultima_notificacion == hora_str:
            return
        self.ultima_notificacion = hora_str
        self.logger.info(f"Mostrando notificación de reporte para turno {turno_actual} a las {hora_str}")
        # Mostrar messagebox
        respuesta = self._mostrar_messagebox_reporte()
        if respuesta:
            # Usuario seleccionó SÍ
            self.logger.info("Usuario seleccionó SÍ - Activando ventana principal")
            self._activar_ventana_principal()
            self._enviar_sms_opcional()
        else:
            # Usuario seleccionó NO o no respondió
            self.logger.info("Usuario seleccionó NO o no respondió")
        # Guardar último recordatorio
        self.config["ultimo_recordatorio"] = datetime.now().isoformat()
        self._save_config()
    
    def _verificar_hora_periodicamente(self):
        """Hilo principal que verifica la hora cada minuto."""
        self.logger.info("Iniciando verificación periódica de hora")
        
        while self.running:
            try:
                self._procesar_notificacion_reporte()
                
                # Esperar hasta el siguiente minuto
                ahora = datetime.now()
                segundos_restantes = 60 - ahora.second
                time_module.sleep(segundos_restantes)
                
            except Exception as e:
                self.logger.error(f"Error en verificación periódica: {e}")
                time_module.sleep(60)  # Esperar 1 minuto en caso de error
    
    def iniciar(self):
        """Inicia el sistema de notificaciones."""
        if self.running:
            self.logger.warning("Sistema ya está ejecutándose")
            return
        
        self.logger.info("Iniciando sistema de notificaciones")
        
        # Mostrar notificación inicial
        self._mostrar_notificacion_inicial()
        
        # Iniciar hilo de verificación
        self.running = True
        self.notification_thread = threading.Thread(
            target=self._verificar_hora_periodicamente,
            daemon=True
        )
        self.notification_thread.start()
        
        self.logger.info("Sistema de notificaciones iniciado correctamente")
    
    def detener(self):
        """Detiene el sistema de notificaciones."""
        if not self.running:
            return
        
        self.logger.info("Deteniendo sistema de notificaciones")
        self.running = False
        
        if self.notification_thread and self.notification_thread.is_alive():
            self.notification_thread.join(timeout=5)
        
        if self.root is not None:
            try:
                self.root.destroy()
                self.root = None
            except:
                pass
        
        self.logger.info("Sistema de notificaciones detenido")
    
    def obtener_estado(self) -> Dict:
        """Retorna el estado actual del sistema."""
        turno_actual = self._determinar_turno_actual()
        hora_actual = self._get_hora_actual()
        
        return {
            "ejecutando": self.running,
            "turno_actual": turno_actual,
            "hora_actual": hora_actual.strftime("%H:%M:%S"),
            "ultimo_recordatorio": self.config.get("ultimo_recordatorio"),
            "notificacion_inicial_mostrada": self.config.get("notificacion_inicial_mostrada", False)
        }

# Instancia global del sistema
_sistema_notificaciones = None

def iniciar_sistema_notificaciones(view=None):
    """Función pública para iniciar el sistema de notificaciones."""
    global _sistema_notificaciones
    
    if _sistema_notificaciones is None:
        _sistema_notificaciones = SistemaNotificaciones(view=view)
    
    _sistema_notificaciones.iniciar()
    return _sistema_notificaciones

def detener_sistema_notificaciones():
    """Función pública para detener el sistema de notificaciones."""
    global _sistema_notificaciones
    
    if _sistema_notificaciones:
        _sistema_notificaciones.detener()

def obtener_estado_sistema():
    """Función pública para obtener el estado del sistema."""
    global _sistema_notificaciones
    
    if _sistema_notificaciones:
        return _sistema_notificaciones.obtener_estado()
    return {"ejecutando": False}

# Función de compatibilidad con el código existente
def notificacion(parent=None):
    """Función de compatibilidad para mantener la interfaz existente."""
    return iniciar_sistema_notificaciones()

# Ejecutar automáticamente si se ejecuta este archivo directamente
if __name__ == "__main__":
    try:
        sistema = iniciar_sistema_notificaciones()
        print("🔔 Sistema de notificaciones iniciado")
        print("Presiona Ctrl+C para detener...")
        
        # Mantener el programa ejecutándose
        try:
            while True:
                time_module.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo sistema de notificaciones...")
            detener_sistema_notificaciones()
            print("✅ Sistema detenido correctamente")
            
    except Exception as e:
        print(f"❌ Error al iniciar sistema de notificaciones: {e}")
        logging.error(f"Error fatal en sistema de notificaciones: {e}")