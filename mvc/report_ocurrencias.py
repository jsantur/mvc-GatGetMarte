import tkinter as tk
from tkinter import ttk, scrolledtext
import pyperclip
from datetime import datetime
import json
import os
import sys
import google.generativeai as genai
import platform
import urllib.request
import urllib.error
import socket
import re
import threading
from spellchecker import SpellChecker
import logging
from PIL import Image, ImageTk

# Importar LanguageTool para corrección offline avanzada (opcional)
try:
    import language_tool_python
    LANGUAGETOOL_AVAILABLE = True
except ImportError:
    LANGUAGETOOL_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.info("LanguageTool no disponible, usando pyspellchecker como corrector local")

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constantes de Configuración (mismo que en report_unidades.py)
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
    'WINDOW_SIZE': '700x800',
    'PADDING': {'small': 5, 'medium': 10, 'large': 20},
    'ICONS': {
        'clock': '🕒', 'calendar': '📅', 'users': '👥', 'police': '🚓', 'report': '📋', 'user': '👤',
        'warning': '⚠️', 'success': '✅', 'copy': '📤'
    }
}

# Lista de cámaras para autocompletado
CAMARAS_LISTA = [
    "Ignacio Merino", "Óvalo Punta Arenas", "Av. G", "Av. H Colegios", "Clinica Tresa", "Niño Héroe",
    "La Parada", "Intercom la Parada", "MORGUE", "Montero", "Palacio Municipal", "Pipos", "Mavila Apra",
    "Iglesia la Inmaculada", "Zona de Bancos", "Curacao BCP", "Caja Piura", "Parque 16", "Parque 17 y 14",
    "Parque 10", "Grifo San Martín", "SENATI", "Toyota", "Intercom. Toyota", "Poste 08 Toyota",
    "PTZ Poste Inmaculada", "Intercom. Inmaculada", "Poste 04 Mavila Centro Cívico", "Intercom. Mavila",
    "LRP Punta Arenas", "Troncos", "Salida a Lobitos", "Puente Yale", "Puente Víctor Raúl",
    "PTZ Poste 10 Plazuela Pescador", "Posta Cono Norte", "Pollería Maruja", "Politécnico",
    "Plazuela Pescador", "Plazuela Cáceres", "Pecata", "Parcela 25", "Muelle Uno", "Mercado Acapulco",
    "Max Cornejo Pacora", "Malecón San Pedro", "Intercom Primax", "Intercom Plazuela Pescador",
    "Grifo Primax", "Grifo Acapulco", "Estadio Campeonísimo", "EsSalud", "Cocobongo",
    "Cámara PTZ Poste Primax", "Base Cono Norte", "FONAVI", "Coliseo Los Pinos", "María Reina de la Paz",
    "Óvalo Urba", "Iglesia Señor de los Milagros", "Calle 01 Talara Alta", "SAPISA", "Parque 28 de Julio",
    "Tanque Víctor Raúl", "Posta Quiñones", "Plazuela Quiñones", "Colegio Señor de los Milagros",
    "Escuela de San Sebastián", "Paradero 20", "Colegio 13", "Cola de Gato", "Cuadrado del Agua",
    "Gruta Jorge Chávez", "Pilar Nores", "Chatarreros", "Mario Aguirre", "CORPAC", "07 de Junio",
    "PTZ Poste Óvalo de la Urba", "Intercom Óvalo Urba", "Poste 06 Gruta Jorge Chávez",
    "Intercom Gruta Jorge Chávez", "Poste 07 Aeropuerto", "Intercom Aeropuerto", "Poste 09 Víctor Raúl",
    "Intercom Víctor Raúl", "Sacobsa", "Grifo Challe N.T", "Negreiros-Luciano", "Tanque Elevado",
    "Enace II Antena", "Poste Ovalo Urba"
]

# Clase para manejar el autocompletado de cámaras
class AutocompletadoCamaras:
    def __init__(self, entry_widget, lista_camaras):
        self.entry = entry_widget
        self.lista_camaras = lista_camaras
        self.popup = None
        self.listbox = None
        self.filtrado = []
        self._ignore_focus_out = False  # Bandera para evitar cierre abrupto

        # Vincular eventos
        self.entry.bind('<KeyRelease>', self._on_key_release)
        self.entry.bind('<Down>', self._on_down)
        self.entry.bind('<Up>', self._on_up)
        self.entry.bind('<Return>', self._on_return)
        self.entry.bind('<Escape>', self._on_escape)
        self.entry.bind('<FocusOut>', self._on_focus_out)
        self.entry.bind('<Tab>', self._on_tab)  # Autocompletar con TAB
        
    def _on_key_release(self, event):
        if event.keysym in ['Down', 'Up', 'Return', 'Escape']:
            return
        
        self._filtrar_sugerencias()
        
    def _filtrar_sugerencias(self):
        texto = self.entry.get().strip().lower()
        if len(texto) < 1:
            self._ocultar_popup()
            return

        # Búsqueda mejorada: prioritarias las que empiezan con el texto
        starts = [c for c in self.lista_camaras if c.lower().startswith(texto)]
        # Luego las que contienen el texto pero no empiezan con él
        contains = [c for c in self.lista_camaras if texto in c.lower() and c not in starts]

        self.filtrado = starts + contains

        if self.filtrado:
            self._mostrar_popup()
        else:
            self._ocultar_popup()
            
    def _mostrar_popup(self):
        if self.popup:
            self.popup.destroy()

        # Crear ventana popup
        self.popup = tk.Toplevel(self.entry)
        self.popup.overrideredirect(True)
        self.popup.configure(bg=UI_CONSTANTS['COLORS']['card_bg'])
        self.popup.attributes('-topmost', True)

        # Crear listbox más ancho para mejor visibilidad
        self.listbox = tk.Listbox(self.popup,
                                 font=UI_CONSTANTS['FONTS']['body'],
                                 bg=UI_CONSTANTS['COLORS']['card_bg'],
                                 fg=UI_CONSTANTS['COLORS']['text_primary'],
                                 selectbackground=UI_CONSTANTS['COLORS']['secondary'],
                                 selectforeground='white',
                                 relief='solid',
                                 borderwidth=1,
                                 height=min(len(self.filtrado), 8))

        # Agregar elementos filtrados
        for camara in self.filtrado:
            self.listbox.insert(tk.END, camara)

        self.listbox.pack(fill=tk.BOTH, expand=True)

        # Vincular eventos del listbox - selección con un clic y doble clic
        self.listbox.bind('<ButtonRelease-1>', self._on_select)  # Un solo clic
        self.listbox.bind('<Double-Button-1>', self._on_select)  # Doble clic (legacy)
        self.listbox.bind('<Return>', self._on_select)

        # Capturar eventos de entrada/salida del mouse para evitar cierre abrupto
        self.popup.bind('<Enter>', lambda e: setattr(self, '_ignore_focus_out', True))
        self.popup.bind('<Leave>', lambda e: setattr(self, '_ignore_focus_out', False))

        # Posicionar popup debajo del entry (más ancho para mejor visibilidad)
        self._posicionar_popup()
        
    def _posicionar_popup(self):
        if not self.popup:
            return

        # Obtener posición del entry
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        entry_width = self.entry.winfo_width()

        # Calcular ancho máximo necesario basado en el contenido
        max_width = entry_width
        if self.listbox:
            for item in self.filtrado[:8]:  # Solo revisar los primeros 8 items visibles
                item_width = len(item) * 8  # Aproximadamente 8px por caracter
                max_width = max(max_width, min(item_width, 400))  # Máximo 400px

        # Posicionar popup (más ancho para mejor visibilidad)
        popup_width = max(max_width, entry_width)
        self.popup.geometry(f"{int(popup_width)}x{min(len(self.filtrado) * 25 + 10, 200)}")
        self.popup.geometry(f"+{x}+{y}")
        
    def _ocultar_popup(self):
        if self.popup:
            self.popup.destroy()
            self.popup = None
            self.listbox = None
            
    def _on_down(self, event):
        if self.listbox:
            try:
                current = self.listbox.curselection()[0]
                if current < len(self.filtrado) - 1:
                    self.listbox.selection_clear(0, tk.END)
                    self.listbox.selection_set(current + 1)
                    self.listbox.see(current + 1)
            except IndexError:
                if self.filtrado:
                    self.listbox.selection_set(0)
        return 'break'
        
    def _on_up(self, event):
        if self.listbox:
            try:
                current = self.listbox.curselection()[0]
                if current > 0:
                    self.listbox.selection_clear(0, tk.END)
                    self.listbox.selection_set(current - 1)
                    self.listbox.see(current - 1)
            except IndexError:
                if self.filtrado:
                    self.listbox.selection_set(len(self.filtrado) - 1)
        return 'break'
        
    def _on_return(self, event):
        if self.listbox and self.listbox.curselection():
            self._on_select(event)
        return 'break'
        
    def _on_escape(self, event):
        if self.popup:
            self._ocultar_popup()
            return 'break'
        # Si no hay popup, permitir que el evento se propague
        return None
        
    def _on_focus_out(self, event):
        # Solo ocultar si el nuevo foco no está dentro del popup
        if self.popup and not self._ignore_focus_out:
            self.entry.after(300, self._ocultar_popup)
        
    def _on_select(self, event):
        if self.listbox and self.listbox.curselection():
            seleccion = self.listbox.get(self.listbox.curselection())
            self.entry.delete(0, tk.END)
            self.entry.insert(0, seleccion)
            self._ocultar_popup()
            self.entry.focus_set()
            return 'break'

    def _on_tab(self, event):
        """Autocompletar con la primera sugerencia al presionar TAB."""
        if self.filtrado and self.popup:
            seleccion = self.filtrado[0]
            self.entry.delete(0, tk.END)
            self.entry.insert(0, seleccion)
            self._ocultar_popup()
            return 'break'
        return None

# Función para manejar rutas en modo .py y .exe
def resource_path(relative_path):
    """Obtiene la ruta correcta para recursos en modo desarrollo y ejecutable."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Clase para verificar la conexión a internet
class InternetChecker:
    @staticmethod
    def check_internet_connection(timeout=5):
        test_urls = ['https://8.8.8.8', 'https://1.1.1.1', 'https://google.com']
        for url in test_urls:
            try:
                urllib.request.urlopen(url, timeout=timeout)
                return True
            except (urllib.error.URLError, socket.timeout) as e:
                logger.warning(f"Fallo al conectar a {url}: {e}")
                continue
        return False

# Clase para corrección ortográfica local (LanguageTool como principal, pyspellchecker como fallback)
class LocalSpellChecker:
    def __init__(self):
        self.lt = None
        self.spell_es = None
        self.spell_en = None
        self._init_language_tool()

    def _init_language_tool(self):
        """Intenta inicializar LanguageTool, si falla usa pyspellchecker."""
        if LANGUAGETOOL_AVAILABLE:
            try:
                # Descarga el modelo de español (solo la primera vez, ~300 MB)
                self.lt = language_tool_python.LanguageTool('es')
                logger.info("LanguageTool inicializado correctamente (es)")
                return
            except Exception as e:
                logger.warning(f"No se pudo inicializar LanguageTool: {e}")
                self.lt = None

        # Fallback a pyspellchecker
        try:
            self.spell_es = SpellChecker(language='es')
            self.spell_en = SpellChecker(language='en')
            logger.info("pyspellchecker inicializado como fallback")
        except Exception as e:
            logger.error(f"Error inicializando SpellChecker: {e}")
            self.spell_es = None
            self.spell_en = None

    def correct_text(self, texto):
        """Corrige texto usando LanguageTool si está disponible, sino pyspellchecker."""
        if self.lt:
            return self._correct_with_languagetool(texto)
        elif self.spell_es or self.spell_en:
            return self._correct_with_spellchecker(texto)
        else:
            logger.warning("Ningún corrector disponible, usando solo formateo básico")
            return self._apply_basic_formatting(texto)

    def _correct_with_languagetool(self, texto):
        """Corrige usando LanguageTool (más completo: ortografía, gramática, puntuación)."""
        try:
            # LanguageTool devuelve sugerencias más completas
            matches = self.lt.check(texto)
            corrected = language_tool_python.utils.correct(texto, matches)
            return self._apply_basic_formatting(corrected)
        except Exception as e:
            logger.error(f"Error en corrección con LanguageTool: {e}")
            # Fallback al spellchecker si LanguageTool falla
            if self.spell_es or self.spell_en:
                return self._correct_with_spellchecker(texto)
            return self._apply_basic_formatting(texto)

    def _correct_with_spellchecker(self, texto):
        """Corrige usando pyspellchecker (fallback simple)."""
        try:
            words = re.findall(r'\b\w+\b', texto)
            corrected_text, offset = texto, 0
            for start, end, word in [(texto.find(w), texto.find(w) + len(w), w) for w in words]:
                adj_start, adj_end = start + offset, end + offset
                if word.lower() in self.spell_es or word.lower() in self.spell_en:
                    continue
                candidates = self.spell_es.candidates(word.lower()) or self.spell_en.candidates(word.lower())
                if candidates:
                    correction = list(candidates)[0]
                    if word.isupper():
                        correction = correction.upper()
                    elif word.istitle():
                        correction = correction.title()
                    corrected_text = corrected_text[:adj_start] + correction + corrected_text[adj_end:]
                    offset += len(correction) - len(word)
            return self._apply_basic_formatting(corrected_text)
        except Exception as e:
            logger.error(f"Error en corrección con spellchecker: {e}")
            return self._apply_basic_formatting(texto)

    def _apply_basic_formatting(self, texto):
        """Aplica formato básico: mayúsculas después de punto, espacios correctos."""
        texto = re.sub(r'(\. )([a-z])', lambda m: m.group(1) + m.group(2).upper(), texto)
        if texto and texto[0].islower():
            texto = texto[0].upper() + texto[1:]
        return re.sub(r'\s+', ' ', re.sub(r'([,.;:!?])([A-Za-z])', r'\1 \2', re.sub(r'\s+([,.;:!?])', r'\1', texto))).strip()

# Clase para gestionar la configuración de la API de Gemini
class APIConfigManager:
    CONFIG_FILE = "gemini_config.json"

    @classmethod
    def load_config(cls):
        config_path = resource_path(cls.CONFIG_FILE)
        default_config = {"api_key": "AIzaSyBPB2pfeVAD0D6BFIja_mOePQvOk0qIlck"}
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    if config_data.get("api_key"):
                        return config_data
            cls.save_config(default_config["api_key"])
            return default_config
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            return default_config

    @classmethod
    def save_config(cls, api_key):
        config_path = resource_path(cls.CONFIG_FILE)
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({"api_key": api_key}, f)
        except Exception as e:
            logger.warning(f"No se pudo guardar config: {e}")

    @classmethod
    def get_api_key(cls, parent_window):
        config = cls.load_config()
        api_key = config.get("api_key")
        if api_key and cls.validate_api_key(api_key):
            return api_key
        ToastNotification(parent_window, "API Key de Gemini no configurada o inválida.", "⚠️ Advertencia")
        return None

    @staticmethod
    def validate_api_key(api_key):
        try:
            genai.configure(api_key=api_key)
            genai.list_models()
            return True
        except Exception as e:
            logger.error(f"API Key inválida: {e}")
            return False

# Clase para notificaciones emergentes
class ToastNotification(tk.Toplevel):
    def __init__(self, parent, message, title="Notificación", duration=3000):
        tk.Toplevel.__init__(self, parent)
        self.title(title)
        self.message = message
        self.duration = duration
        self.configure(bg=UI_CONSTANTS['COLORS']['card_bg'])
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        
        # Configurar el frame principal
        main_frame = tk.Frame(self, bg=UI_CONSTANTS['COLORS']['card_bg'], relief='solid', borderwidth=1)
        main_frame.pack(padx=2, pady=2)
        
        # Frame para el contenido
        content_frame = tk.Frame(main_frame, bg=UI_CONSTANTS['COLORS']['card_bg'])
        content_frame.pack(padx=15, pady=10)
        
        # Mensaje
        message_label = tk.Label(content_frame, text=message, 
                               font=UI_CONSTANTS['FONTS']['small'], 
                               fg=UI_CONSTANTS['COLORS']['text_primary'], 
                               bg=UI_CONSTANTS['COLORS']['card_bg'],
                               wraplength=300, justify='center')
        message_label.pack(pady=(0, 8))
        
        # Frame para botones centrados
        button_frame = tk.Frame(content_frame, bg=UI_CONSTANTS['COLORS']['card_bg'])
        button_frame.pack()
        
        # Botón de cerrar centrado
        close_button = tk.Button(button_frame, text="Cerrar", 
                               font=UI_CONSTANTS['FONTS']['small'],
                               fg='white', bg=UI_CONSTANTS['COLORS']['secondary'],
                               relief='flat', borderwidth=0,
                               command=self.destroy,
                               padx=20, pady=3)
        close_button.pack()
        
        # Configurar hover effect
        def on_enter(e):
            close_button.configure(bg='#2980b9')
        def on_leave(e):
            close_button.configure(bg=UI_CONSTANTS['COLORS']['secondary'])
        
        close_button.bind('<Enter>', on_enter)
        close_button.bind('<Leave>', on_leave)

        # Posicionar en la esquina inferior derecha
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.update_idletasks()
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        position_right = screen_width - window_width - 20
        position_down = screen_height - window_height - 50
        self.geometry(f"+{position_right}+{position_down}")

        # Auto-cerrar después del tiempo especificado
        self.after(duration, self.destroy)

# Clase principal para la ventana de ocurrencias
class OcurrenciasWindow:
    _window_open = False

    def __init__(self, parent, turno=None):
        if OcurrenciasWindow._window_open:
            ToastNotification(parent, "La ventana de ocurrencias ya está abierta 📝", "⚠️ Advertencia")
            return
        self.api_key = APIConfigManager.get_api_key(parent)
        self.local_checker = LocalSpellChecker()
        self.internet_available = InternetChecker.check_internet_connection()
        if self.internet_available and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
            except Exception as e:
                ToastNotification(parent, f"Error configurando Gemini API: {e}", "⚠️ Advertencia")
                self.api_key = None
        self.parent = parent
        self.turno = turno or "DÍA"
        self.create_window()
        OcurrenciasWindow._window_open = True

    def create_window(self):
        try:
            self.window = tk.Toplevel(self.parent)
            self.window.title("📝 Reporte de Ocurrencias")
            self.window.geometry(UI_CONSTANTS['WINDOW_SIZE'])
            self.window.resizable(False, False)
            self.window.attributes('-topmost', True)
            self.window.protocol("WM_DELETE_WINDOW", lambda: None)
            self.window.configure(bg=UI_CONSTANTS['COLORS']['background'])
            self.window.bind('<Escape>', lambda e: self._on_close())
            self.window.bind('<Control-Return>', lambda e: self._procesar_con_corrector())
            self.window.bind('<Control-c>', lambda e: self._copy_to_clipboard())

            self.font_base = UI_CONSTANTS['FONTS']['body']
            self.font_titulo = UI_CONSTANTS['FONTS']['title']
            self.font_resultado = UI_CONSTANTS['FONTS']['mono']

            header_frame = tk.Frame(self.window, bg=UI_CONSTANTS['COLORS']['primary'], height=70)
            header_frame.pack(fill=tk.X, pady=(0, UI_CONSTANTS['PADDING']['large']))
            
            # Contenedor principal para imagen y textos
            content_frame = tk.Frame(header_frame, bg=UI_CONSTANTS['COLORS']['primary'])
            content_frame.pack(expand=True, fill=tk.BOTH, padx=(150, 15), pady=3)
            
            # Cargar y mostrar la imagen
            try:
                image_path = os.path.join("help", "Ocurrencias.png")
                if os.path.exists(image_path):
                    # Cargar imagen y redimensionar a 100x100
                    original_image = Image.open(image_path)
                    resized_image = original_image.resize((100, 100), Image.Resampling.LANCZOS)
                    self.logo_image = ImageTk.PhotoImage(resized_image)
                    
                    # Frame para la imagen
                    image_frame = tk.Frame(content_frame, bg=UI_CONSTANTS['COLORS']['primary'])
                    image_frame.pack(side=tk.LEFT, padx=(0, 5))
                    
                    logo_label = tk.Label(image_frame, image=self.logo_image, bg=UI_CONSTANTS['COLORS']['primary'])
                    logo_label.pack()
                else:
                    # Si no existe la imagen, crear un placeholder
                    image_frame = tk.Frame(content_frame, bg=UI_CONSTANTS['COLORS']['primary'], width=100, height=100)
                    image_frame.pack(side=tk.LEFT, padx=(0, 5))
                    image_frame.pack_propagate(False)
            except Exception as e:
                # En caso de error, crear un placeholder
                image_frame = tk.Frame(content_frame, bg=UI_CONSTANTS['COLORS']['primary'], width=100, height=100)
                image_frame.pack(side=tk.LEFT, padx=(0, 5))
                image_frame.pack_propagate(False)
            
            # Frame para los textos
            text_frame = tk.Frame(content_frame, bg=UI_CONSTANTS['COLORS']['primary'])
            text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Título principal
            title_label = tk.Label(text_frame, text="REPORTE DE OCURRENCIAS", 
                                  font=self.font_titulo, bg=UI_CONSTANTS['COLORS']['primary'], fg='white')
            title_label.pack(anchor=tk.W, pady=(0, 0))
            
            # Subtítulo con funcionalidades
            subtitle_label = tk.Label(text_frame, text="Corrector con IA • Sugerencias al escribir cámara • Copia rápida", 
                                     font=UI_CONSTANTS['FONTS']['small'], bg=UI_CONSTANTS['COLORS']['primary'], fg='#bdc3c7')
            subtitle_label.pack(anchor=tk.W, pady=(0, 0))
            
            # Instrucción
            instruction_label = tk.Label(text_frame, text="💡 Presiona ESC para cerrar la ventana", 
                                        font=UI_CONSTANTS['FONTS']['small'], bg=UI_CONSTANTS['COLORS']['primary'], fg='#FFD700')
            instruction_label.pack(anchor=tk.W)

            status_frame = tk.Frame(self.window, bg=UI_CONSTANTS['COLORS']['background'])
            status_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
            self._create_status_indicator(status_frame)

            main_frame = tk.Frame(self.window, bg=UI_CONSTANTS['COLORS']['background'], padx=20, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            main_frame.bind('<Escape>', lambda e: self._on_close())

            input_frame = ttk.LabelFrame(main_frame, text="Datos de la Ocurrencia", padding=UI_CONSTANTS['PADDING']['medium'], style='Modern.TLabelframe')
            input_frame.pack(fill=tk.X, pady=(0, 20))

            camera_time_row = tk.Frame(input_frame, bg=UI_CONSTANTS['COLORS']['card_bg'])
            camera_time_row.pack(fill=tk.X, pady=(0, 10))
            tk.Label(camera_time_row, text="📷 Cámara:", font=self.font_base, bg=UI_CONSTANTS['COLORS']['card_bg']).pack(side=tk.LEFT)
            self.camara_entry = ttk.Entry(camera_time_row, font=self.font_base, width=25)
            self.camara_entry.pack(side=tk.LEFT, padx=(5, 20), expand=True, fill=tk.X)
            
            # Configurar autocompletado para el campo de cámara
            self.autocompletado_camaras = AutocompletadoCamaras(self.camara_entry, CAMARAS_LISTA)
            
            self.camara_entry.focus_set()
            tk.Label(camera_time_row, text="🕒 Hora:", font=self.font_base, bg=UI_CONSTANTS['COLORS']['card_bg']).pack(side=tk.LEFT)
            self.hora_entry = ttk.Entry(camera_time_row, font=self.font_base, width=8)
            self.hora_entry.pack(side=tk.LEFT, padx=5)
            self.hora_entry.insert(0, datetime.now().strftime("%H:%M"))

            tk.Label(input_frame, text="📝 Descripción de la ocurrencia:", font=self.font_base, bg=UI_CONSTANTS['COLORS']['card_bg']).pack(anchor="w", pady=(5, 0))
            self.texto_ocurrencia = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, width=80, height=8, font=self.font_base, padx=8, pady=8, relief="flat", borderwidth=2)
            self.texto_ocurrencia.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            self.texto_ocurrencia.bind('<Escape>', lambda e: self._on_close())

            action_frame = tk.Frame(main_frame, bg=UI_CONSTANTS['COLORS']['background'])
            action_frame.pack(fill=tk.X, pady=(10, 20))
            
            # Frame centrado para los botones
            buttons_center_frame = tk.Frame(action_frame, bg=UI_CONSTANTS['COLORS']['background'])
            buttons_center_frame.pack(expand=True)
            
            # Botones sin width fijo para mostrar todo el contenido
            ttk.Button(buttons_center_frame, text="📤 Generar y Copiar Reporte", 
                      command=self._procesar_con_corrector, 
                      style='Ocurrencias.Primary.TButton').pack(side=tk.LEFT, padx=5)
            ttk.Button(buttons_center_frame, text="🖨️ Imprimir", 
                      command=self._imprimir_ocurrencias, 
                      style='Ocurrencias.Secondary.TButton').pack(side=tk.LEFT, padx=5)

            output_frame = ttk.LabelFrame(main_frame, text="Reporte Generado", padding=UI_CONSTANTS['PADDING']['medium'], style='Modern.TLabelframe')
            output_frame.pack(fill=tk.BOTH, expand=True)
            output_frame.bind('<Escape>', lambda e: self._on_close())
            tk.Label(output_frame, text="✏️ Texto corregido y formateado:", font=self.font_base, bg=UI_CONSTANTS['COLORS']['card_bg']).pack(anchor="w", pady=(5, 0))
            self.resultado_text = tk.Text(output_frame, wrap=tk.WORD, width=80, height=12, font=self.font_resultado, bg='#f8f9fa', fg=UI_CONSTANTS['COLORS']['text_primary'], padx=10, pady=10, state='disabled', relief="flat", borderwidth=1)
            self.resultado_text.pack(fill=tk.BOTH, expand=True)

            self._configure_styles()

            # Barra de estado inferior
            self._create_status_bar()
        except Exception as e:
            logger.error(f"Error creando ventana: {e}")
            ToastNotification(self.parent, f"No se pudo abrir la ventana: {e}", "❌ Error")

    def _create_status_indicator(self, parent):
        indicator_frame = tk.Frame(parent, bg=UI_CONSTANTS['COLORS']['background'])
        indicator_frame.pack(fill=tk.X)
        connection_text = "🌐 Internet: Conectado" if self.internet_available else "🔴 Internet: Sin conexión"
        connection_color = UI_CONSTANTS['COLORS']['success'] if self.internet_available else UI_CONSTANTS['COLORS']['error']
        self.connection_label = tk.Label(indicator_frame, text=connection_text, font=UI_CONSTANTS['FONTS']['small'], fg=connection_color, bg=UI_CONSTANTS['COLORS']['background'])
        self.connection_label.pack(side=tk.LEFT)
        tk.Label(indicator_frame, text=" | ", font=UI_CONSTANTS['FONTS']['small'], fg=UI_CONSTANTS['COLORS']['text_secondary'], bg=UI_CONSTANTS['COLORS']['background']).pack(side=tk.LEFT)
        method_text = "🤖 Método: Gemini AI" if self.internet_available and self.api_key else "🔧 Método: Local (pyspellchecker)"
        method_color = UI_CONSTANTS['COLORS']['secondary'] if self.internet_available and self.api_key else UI_CONSTANTS['COLORS']['warning']
        self.method_label = tk.Label(indicator_frame, text=method_text, font=UI_CONSTANTS['FONTS']['small'], fg=method_color, bg=UI_CONSTANTS['COLORS']['background'])
        self.method_label.pack(side=tk.LEFT)
        tk.Button(indicator_frame, text="🔄", font=UI_CONSTANTS['FONTS']['small'], command=self._refresh_connection_status, bg=UI_CONSTANTS['COLORS']['background'], relief="flat", borderwidth=0).pack(side=tk.RIGHT)

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Modern.TLabelframe', background=UI_CONSTANTS['COLORS']['card_bg'], borderwidth=1, relief='solid')
        style.configure('Modern.TLabelframe.Label', background=UI_CONSTANTS['COLORS']['card_bg'], foreground=UI_CONSTANTS['COLORS']['text_primary'], font=UI_CONSTANTS['FONTS']['subtitle'])
        # Estilos únicos para ocurrencias para evitar conflictos
        style.configure('Ocurrencias.Primary.TButton', font=UI_CONSTANTS['FONTS']['subtitle'], padding=(20, 10), foreground='white', background=UI_CONSTANTS['COLORS']['secondary'])
        style.map('Ocurrencias.Primary.TButton', background=[('active', '#2980b9'), ('pressed', '#21618c')])
        style.configure('Ocurrencias.Secondary.TButton', font=UI_CONSTANTS['FONTS']['subtitle'], padding=(20, 10), foreground='white', background=UI_CONSTANTS['COLORS']['secondary'])
        style.map('Ocurrencias.Secondary.TButton', background=[('active', '#2980b9'), ('pressed', '#21618c')])

    def _procesar_con_corrector(self):
        texto_original = self.texto_ocurrencia.get("1.0", tk.END).strip()
        if not texto_original:
            ToastNotification(self.window, "Por favor ingrese la descripción de la ocurrencia", "⚠️ Advertencia")
            return
        self._check_connection_status()
        threading.Thread(target=self._procesar_reporte, args=(texto_original, self.camara_entry.get().strip(), self.hora_entry.get().strip())).start()

    def _procesar_reporte(self, texto_original, camara, hora_manual):
        try:
            texto_corregido, metodo_usado = (self._corregir_con_gemini(texto_original), "Gemini AI") if self.internet_available and self.api_key else (self._corregir_localmente(texto_original), "Local (pyspellchecker)")
            texto_portapapeles = self._format_report(texto_corregido, camara, hora_manual)
            pyperclip.copy(texto_portapapeles.upper())
            self._mostrar_resultado(texto_portapapeles.upper())
            self._guardar_ocurrencia_json(camara, hora_manual, texto_corregido)
            ToastNotification(self.window, f"Reporte generado con {metodo_usado} y copiado al portapapeles", "Éxito")
            self._update_status("Reporte generado y copiado")
            self._clear_inputs()
        except Exception as e:
            logger.error(f"Error al procesar el reporte: {e}")
            ToastNotification(self.window, f"Error al procesar: {str(e)}", "❌ Error")
            self._update_status("Error al generar reporte")

    def _format_report(self, texto_corregido, camara, hora_manual):
        ahora = datetime.now()
        fecha = ahora.strftime("📅 %Y-%m-%d")
        computer_name = platform.node()
        report = f"📨 REPORTE DE TURNO: {self.turno}\n"
        report += f"🎥 CÁMARA: {camara.upper()}\n" if camara else ""
        report += f"{fecha} | 🕒 {hora_manual}\n📝 OCURRENCIA:\n    {texto_corregido.replace('\n', '\n    ')}\n\n👤 USUARIO: {computer_name.upper()}\n----------------------------------------"
        return report

    def _corregir_con_gemini(self, texto):
        prompt = f"Actúa como un editor profesional especializado en redacción técnica para informes de seguridad. Reescribe el siguiente texto con redacción clara, concisa y profesional, adecuada para reportes operativos o de vigilancia. Corrige errores gramaticales, ortográficos y de puntuación. Mejora la estructura sin alterar el sentido original. Usa mayúsculas para términos clave. Texto original:\n\n{texto}\n\nDevuelve solo el texto corregido."
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.3, max_output_tokens=1000))
        return response.text.strip()

    def _corregir_localmente(self, texto):
        return self.local_checker.correct_text(texto)

    def _mostrar_resultado(self, texto):
        self.resultado_text.config(state='normal')
        self.resultado_text.delete("1.0", tk.END)
        self.resultado_text.insert(tk.END, texto)
        self.resultado_text.config(state='disabled')

    def _clear_inputs(self):
        self.camara_entry.delete(0, tk.END)
        self.texto_ocurrencia.delete("1.0", tk.END)
        self.camara_entry.focus_set()

    def _copy_to_clipboard(self):
        try:
            text = self.resultado_text.get("1.0", tk.END).strip()
            if text:
                pyperclip.copy(text)
                ToastNotification(self.window, "Reporte copiado al portapapeles", "Éxito")
                self._update_status("Reporte copiado al portapapeles")
        except Exception as e:
            ToastNotification(self.window, f"Error al copiar: {str(e)}", "❌ Error")
            self._update_status("Error al copiar reporte")

    def _on_close(self):
        OcurrenciasWindow._window_open = False
        self.window.destroy()

    def _check_connection_status(self):
        self.internet_available = InternetChecker.check_internet_connection()
        self.connection_label.config(text="🌐 Internet: Conectado" if self.internet_available else "🔴 Internet: Sin conexión", fg=UI_CONSTANTS['COLORS']['success'] if self.internet_available else UI_CONSTANTS['COLORS']['error'])
        self.method_label.config(text="🤖 Método: Gemini AI" if self.internet_available and self.api_key else "🔧 Método: Local (pyspellchecker)", fg=UI_CONSTANTS['COLORS']['secondary'] if self.internet_available and self.api_key else UI_CONSTANTS['COLORS']['warning'])

    def _refresh_connection_status(self):
        self._check_connection_status()

    def _create_status_bar(self):
        self.status_bar = tk.Frame(self.window, bg=UI_CONSTANTS['COLORS']['primary'], height=25)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label = tk.Label(self.status_bar, text="Listo para generar reporte", bg=UI_CONSTANTS['COLORS']['primary'],
                                     fg='white', font=UI_CONSTANTS['FONTS']['small'])
        self.status_label.pack(side=tk.LEFT, padx=5)
        tk.Label(self.status_bar, text=f"🪪 Usuario: {platform.node().upper()}", bg=UI_CONSTANTS['COLORS']['primary'],
                 fg='white', font=UI_CONSTANTS['FONTS']['small']).pack(side=tk.RIGHT, padx=5)

    def _update_status(self, message: str):
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            self.status_label.config(text=message)
            self.window.after(5000, lambda: self.status_label.config(text="Listo para generar reporte") if self.status_label.winfo_exists() else None)

    def _guardar_ocurrencia_json(self, camara, hora_manual, texto_corregido):
        fecha = datetime.now().strftime("%Y-%m-%d")
        os.makedirs('reportes_json', exist_ok=True)
        file_path = os.path.join('reportes_json', f'ocurrencias_{fecha}.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
        else:
            all_data = []
        # Formato profesional y claro para el campo 'reporte'
        reporte = (
            f"CÁMARA: {camara}\n"
            f"FECHA  : {fecha}\n"
            f"HORA   : {hora_manual}\n\n"
            f"OCURRENCIA:\n{texto_corregido}\n"
        )
        data = {
            'fecha': fecha,
            'hora': hora_manual,
            'turno': self.turno,
            'camara': camara,
            'ocurrencia': texto_corregido,
            'usuario': platform.node().upper(),
            'reporte': reporte
        }
        all_data.append(data)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

    def _imprimir_ocurrencias(self):
        fecha = datetime.now().strftime("%Y-%m-%d")
        file_path = os.path.join('reportes_json', f'ocurrencias_{fecha}.json')
        if not os.path.exists(file_path):
            ToastNotification(self.window, "No hay ocurrencias almacenadas para hoy", "⚠️ Advertencia")
            return
        with open(file_path, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
        if not all_data:
            ToastNotification(self.window, "No hay ocurrencias para hoy", "⚠️ Advertencia")
            return
        # Ordenar por hora (HH:MM)
        def hora_key(x):
            try:
                return int(x['hora'][:2])*60 + int(x['hora'][3:5])
            except:
                return 0
        all_data.sort(key=hora_key)
        img_path = self._generar_imagen_ocurrencias(all_data)
        if img_path:
            self._previsualizar_imagen(img_path)

    def _generar_imagen_ocurrencias(self, ocurrencias):
        from PIL import Image, ImageDraw, ImageFont
        from textwrap import wrap
        os.makedirs('img', exist_ok=True)
        width = 900
        padding = 40
        line_height = 25
        spacing_between_occurrences = 30
        
        # Calcular altura dinámica basada en el contenido
        total_height = padding * 2 + 60  # Encabezado
        for oc in ocurrencias:
            # Altura para cámara y hora
            total_height += line_height * 2
            # Altura para ocurrencia (aproximadamente 4 líneas por defecto)
            obs_lines = len(wrap(oc['ocurrencia'], width=80))
            total_height += max(obs_lines * line_height, line_height * 3)
            total_height += spacing_between_occurrences
        
        img_path = os.path.join('img', f'ocurrencias_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
        image = Image.new('RGB', (width, total_height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        try:
            font_title = ImageFont.truetype('arial.ttf', 28)
            font_header = ImageFont.truetype('arial.ttf', 20)
            font_body = ImageFont.truetype('arial.ttf', 16)
            font_mono = ImageFont.truetype('consola.ttf', 14)
            # Fuente en negrita para cámara y hora
            font_bold = ImageFont.truetype('arial.ttf', 20)
        except:
            font_title = font_header = font_body = font_mono = font_bold = ImageFont.load_default()
        
        # Encabezado
        encabezado = f'━━━━━━━━━ REPORTE DE OCURRENCIAS ━━━━━━━━━'
        draw.text((width//2 - draw.textlength(encabezado, font=font_title)//2, padding), encabezado, fill=(0,56,147), font=font_title)
        
        y = padding + 60
        
        for idx, oc in enumerate(ocurrencias):
            x = padding
            
            # Cámara
            camara = f"CÁMARA: {oc['camara'].upper()}" if oc['camara'] else ""
            draw.text((x, y), camara, fill=(0,56,147), font=font_bold)
            y += line_height
            
            # Hora
            hora = f"HORA: {oc['hora']} horas"
            draw.text((x, y), hora, fill=(0,0,0), font=font_bold)
            y += line_height
            
            # Ocurrencia con formato mejorado
            obs = oc['ocurrencia']
            # Agregar el prefijo "OBSERVADO:" alineado a la izquierda
            draw.text((x, y), "OBSERVADO:", fill=(0,0,0), font=font_body)
            y += line_height
            
            # Formatear el texto para que se vea más limpio
            obs = obs.replace('. ', '.\n').replace(' - ', '\n- ')
            wrapped_obs = wrap(obs, width=80)
            
            for i, line in enumerate(wrapped_obs):
                if line.strip():
                    draw.text((x+20, y), line.strip(), fill=(0,0,0), font=font_mono)
                    y += line_height
            
            y += spacing_between_occurrences
        
        image.save(img_path)
        return img_path

    def _previsualizar_imagen(self, img_path):
        preview = tk.Toplevel(self.window)
        preview.title('Vista Previa de Ocurrencias')
        img = Image.open(img_path)
        img.thumbnail((900, 1200))
        tk_img = ImageTk.PhotoImage(img)
        label = tk.Label(preview, image=tk_img)
        label.pack()
        self.preview_img = tk_img  # Mantener referencia
        ttk.Button(preview, text='Imprimir', command=lambda: self._imprimir_archivo(img_path)).pack(pady=10)

    def _imprimir_archivo(self, img_path):
        os.startfile(img_path, 'print')

def abrir_ventana_ocurrencias(parent, turno=None):
    OcurrenciasWindow(parent, turno)

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    abrir_ventana_ocurrencias(root)
    root.mainloop()