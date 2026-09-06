# utils.py - Módulo centralizado de utilidades
"""
Módulo centralizado de utilidades para el sistema MVC.
Contiene clases y funciones reutilizables para evitar duplicación de código.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import threading
import time
import os
import sys
from pathlib import Path

# Constantes de UI centralizadas
UI_CONSTANTS = {
    'COLORS': {
        'primary': '#2c3e50', 'secondary': '#3498db', 'accent': '#e74c3c', 'success': '#27ae60',
        'warning': '#f39c12', 'background': '#ecf0f1', 'card_bg': '#ffffff', 'text_primary': '#2c3e50',
        'text_secondary': '#7f8c8d', 'border': '#bdc3c7', 'error': '#e74c3c', 'valid': '#27ae60'
    },
    'FONTS': {
        'title': ('Segoe UI', 16, 'bold'), 'subtitle': ('Segoe UI', 12, 'bold'), 'body': ('Segoe UI', 10),
        'small': ('Segoe UI', 9), 'mono': ('Consolas', 10)
    },
    'WINDOW_SIZE': '750x750',
    'PADDING': {'small': 5, 'medium': 10, 'large': 20},
    'ICONS': {
        'clock': '🕒', 'calendar': '📅', 'users': '👥', 'police': '🚓', 'report': '📋', 'user': '👤',
        'warning': '⚠️', 'success': '✅', 'copy': '📤'
    }
}

class ToastNotification:
    """Clase centralizada para notificaciones toast reutilizable en toda la aplicación."""
    
    def __init__(self, parent, message, duration=3000, position='topright', style='success', font_size=None, width=None):
        self.parent = parent
        self.message = message
        self.duration = duration
        self.position = position
        self.style = style
        self.font_size = font_size
        self.width = width
        self._create_toast()

    def _create_toast(self):
        self.toast = tk.Toplevel(self.parent)
        self.toast.overrideredirect(True)
        self.toast.attributes('-topmost', True)
        
        # Seleccionar color según el estilo
        if self.style == 'success':
            bg_color = UI_CONSTANTS['COLORS']['success']
        elif self.style == 'warning':
            bg_color = UI_CONSTANTS['COLORS']['warning']
        elif self.style == 'error':
            bg_color = UI_CONSTANTS['COLORS']['error']
        else:
            bg_color = UI_CONSTANTS['COLORS']['secondary']
        
        self.toast.configure(bg=bg_color)

        # Ajustar fuente y tamaño
        font = UI_CONSTANTS['FONTS']['small']
        if self.font_size:
            font = (font[0], self.font_size, font[2] if len(font) > 2 else '')
        label = tk.Label(self.toast, text=self.message, 
                        font=font, 
                        bg=bg_color, fg='white', padx=20, pady=15, wraplength=self.width or 400, justify='center')
        label.pack()

        # Ajustar tamaño mínimo si se especifica
        if self.width:
            self.toast.minsize(self.width, 80)
        else:
            self.toast.minsize(400, 80)

        self._position_toast()
        self.toast.after(self.duration, self._destroy_toast)

    def _position_toast(self):
        try:
            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()

            toast_width = self.toast.winfo_reqwidth()
            toast_height = self.toast.winfo_reqheight()

            if self.position == 'topright':
                x = parent_x + parent_width - toast_width - 10
                y = parent_y + 10
            elif self.position == 'bottomright':
                x = parent_x + parent_width - toast_width - 10
                y = parent_y + parent_height - toast_height - 10
            elif self.position == 'topleft':
                x = parent_x + 10
                y = parent_y + 10
            elif self.position == 'bottomleft':
                x = parent_x + 10
                y = parent_y + parent_height - toast_height - 10
            else:  # center
                x = parent_x + parent_width // 2 - toast_width // 2
                y = parent_y + parent_height // 2 - toast_height // 2

            self.toast.geometry(f"+{x}+{y}")
        except Exception:
            # Fallback: posicionar en esquina superior derecha de la pantalla
            screen_width = self.parent.winfo_screenwidth()
            self.toast.geometry(f"+{screen_width-200}+10")

    def _destroy_toast(self):
        try:
            self.toast.destroy()
        except Exception:
            pass

class Validators:
    """Clase centralizada para validaciones reutilizables."""
    
    @staticmethod
    def validate_time(time_str: str) -> bool:
        """Valida formato de hora HH:MM."""
        return bool(re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', time_str))

    @staticmethod
    def validate_date(date_str: str) -> bool:
        """Valida formato de fecha YYYY-MM-DD."""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_numeric(value: str, max_length: int = 6) -> bool:
        """Valida que el valor sea numérico y no exceda la longitud máxima."""
        return value.isdigit() and len(value) <= max_length

    @staticmethod
    def sanitize_observation(text: str) -> str:
        """Sanitiza texto de observaciones."""
        return text.strip().upper()

class LoadingDialog:
    """Ventana modal de carga minimalista para operaciones en la nube."""
    def __init__(self, parent, message="Consultando datos en la nube...", title="Espere por favor"):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.attributes("-topmost", True)
        self.window.resizable(False, False)
        self.window.configure(bg="white")
        
        # Eliminar barra de título para un look más moderno (opcional, pero profesional)
        self.window.overrideredirect(True)
        
        # Tamaño y posición (centrada en el padre)
        w, h = 380, 140
        self.window.geometry(f"{w}x{h}")
        
        # Forzar actualización para obtener dimensiones del padre
        self.parent.update_idletasks()
        px = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (w // 2)
        py = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (h // 2)
        self.window.geometry(f"+{px}+{py}")
        
        # Contenedor con borde
        main_frame = tk.Frame(self.window, bg="white", highlightbackground="#3498db", 
                              highlightthickness=2, relief="flat")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Contenido
        tk.Label(main_frame, text="🛰️", font=("Segoe UI", 28), bg="white").pack(pady=(15, 0))
        tk.Label(main_frame, text=message, font=("Segoe UI", 11, "bold"), 
                 bg="white", fg="#2c3e50").pack(pady=5)
        
        # Barra de progreso indeterminada (estilo visual)
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', length=280)
        self.progress.pack(pady=(5, 15))
        self.progress.start(10)
        
        # Hacerla modal
        self.window.transient(parent)
        self.window.grab_set()

    def close(self):
        """Cierra el diálogo de carga de forma segura."""
        try:
            self.progress.stop()
            self.window.grab_release()
            self.window.destroy()
        except:
            pass

class ModernEntry(ttk.Entry):
    """Widget de entrada moderno con validación y placeholder."""
    
    def __init__(self, parent, uppercase=False, validator=None, placeholder="", **kwargs):
        super().__init__(parent, **kwargs)
        self.uppercase = uppercase
        self.validator = validator
        self.placeholder = placeholder
        self.is_valid = True
        
        if uppercase:
            self.bind('<KeyRelease>', lambda e: self._to_upper_and_validate())
        else:
            self.bind('<KeyRelease>', lambda e: self._validate())
            
        if validator or placeholder:
            self.bind('<FocusOut>', lambda e: self._validate())
        
        if placeholder:
            self._setup_placeholder()

    def _to_upper_and_validate(self):
        self._to_upper()
        self._validate()

    def _to_upper(self):
        pos = self.index(tk.INSERT)
        text = self.get().upper()
        self.delete(0, tk.END)
        self.insert(0, text)
        self.icursor(pos)

    def _validate(self):
        text = self.get()
        # Asegurar que el color sea negro si tiene contenido real
        if text and text != self.placeholder:
            self.configure(foreground='black')
        
        if self.validator:
            self.is_valid = self.validator(text) if text else True
            self.configure(style='Valid.TEntry' if self.is_valid else 'Invalid.TEntry')

    def _setup_placeholder(self):
        self.insert(0, self.placeholder)
        self.configure(foreground='gray')
        self.bind('<FocusIn>', lambda e: [self.delete(0, tk.END), self.configure(foreground='black')] if self.get() == self.placeholder else None)
        self.bind('<FocusOut>', lambda e: [self.insert(0, self.placeholder), self.configure(foreground='gray')] if not self.get() else None)

class ResourceManager:
    """Gestor centralizado de recursos para evitar fugas de memoria."""
    
    def __init__(self):
        self._resources = []
        self._windows = []
        self._threads = []
        self._files = []
        self._lock = threading.Lock()
    
    def register_window(self, window):
        """Registra una ventana para limpieza automática."""
        with self._lock:
            self._windows.append(window)
    
    def register_thread(self, thread):
        """Registra un thread para limpieza automática."""
        with self._lock:
            self._threads.append(thread)
    
    def register_file(self, file_obj):
        """Registra un archivo para cierre automático."""
        with self._lock:
            self._files.append(file_obj)
    
    def cleanup_all(self):
        """Limpia todos los recursos registrados."""
        with self._lock:
            # Cerrar ventanas
            for window in self._windows:
                try:
                    if hasattr(window, 'destroy'):
                        window.destroy()
                except Exception:
                    pass
            
            # Cerrar archivos
            for file_obj in self._files:
                try:
                    if hasattr(file_obj, 'close'):
                        file_obj.close()
                except Exception:
                    pass
            
            # Limpiar listas
            self._windows.clear()
            self._files.clear()
            self._threads.clear()

# Instancia global del gestor de recursos
resource_manager = ResourceManager()

def should_show_unit(unidades_data: Dict[str, Any], alias: str) -> bool:
    """Función centralizada para determinar si mostrar una unidad según el filtro."""
    real_alias = unidades_data.get('alias_unidades', {}).get(alias, alias)
    filtro = unidades_data.get('filtro_activo', 'TODAS')
    
    if filtro == "TODAS":
        return True
    elif filtro == "PICKUP":
        return real_alias in unidades_data.get('camionetas', set())
    elif filtro == "AUTOS":
        return real_alias in unidades_data.get('autos', set())
    elif filtro == "MANUAL":
        return alias in unidades_data.get('unidades_manuales', [])
    
    return True

def get_base_path() -> str:
    """
    Obtiene la ruta base de la aplicación.
    - En desarrollo: El directorio del script.
    - En ejecutable: El directorio donde reside el .exe físico.
    """
    import sys, os
    if getattr(sys, 'frozen', False):
        # El directorio del archivo .exe
        return os.path.dirname(sys.executable)
    # Desarrollo
    return os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path: str) -> str:
    """
    Obtiene la ruta absoluta al recurso empaquetado dentro del EXE o en desarrollo.
    Usa _MEIPASS en entornos PyInstaller frozen.
    """
    import sys, os
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = getattr(sys, '_MEIPASS', get_base_path())
    except Exception:
        base_path = get_base_path()
    return os.path.join(base_path, relative_path)

def safe_file_operation(func):
    """Decorador para operaciones seguras con archivos."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error en operación de archivo: {e}")
            return None
    return wrapper 