import os
import sys
import tkinter as tk
from tkinter import ttk
import re
from PIL import Image, ImageTk
import platform

# Importar utilidades centralizadas
from utils import ToastNotification

class MegafonosWindow:
    _window_open = False
    
    def __init__(self, parent):
        if MegafonosWindow._window_open:
            ToastNotification(parent, "⚠️ La ventana de megáfonos ya está abierta 📢", 2000)
            return
        self.parent = parent
        self.data = self._load_data()
        self.filtered_data = self.data.copy()
        self.current_selection = -1
        self._setup_window()
        self._setup_styles()
        self._create_interface()
        self._setup_bindings()
        MegafonosWindow._window_open = True
        self._keep_on_top()

    def _load_data(self):
        raw_data = [
            ("Ignacio Merino", "236"), ("Ovalo Punta Arenas", "235"), ("Av. G", "234"), ("Av. H Colegios", "233"),
            ("Clínica Tresa", "213"), ("Niño Héroe", "237"), ("La Parada", "232"), ("Intercom la Parada", "MARCAR EL 3"),
            ("MORGUE", "221"), ("Montero", "222"), ("Palacio Municipal", "220"), ("Pipos", "219"), ("Mavila Apra", "217"),
            ("Iglesia la Inmaculada", "218"), ("Zona de Bancos", "216"), ("Curacao", "215"), ("Caja Piura", "214"),
            ("Parque 16", "227"), ("Parque 17 y 14", "223"), ("Parque 10", "224"), ("Grifo San Martin", "238"),
            ("SENATI", "239"), ("Toyota", "240"), ("Intercom. Toyota", "MARCAR EL 8"), ("Poste 08 Toyota", "***"),
            ("PTZ Poste Inmaculada", "***"), ("Intercom. Inmaculada", "MARCAR EL 2"), ("Poste 04 Mavila Centro Cívico", "***"),
            ("Intercom. Mavila", "MARCAR EL 4"), ("LRP Punta Arenas", "***"), ("Troncos", "245"), ("Salida a Lobitos", "200"),
            ("Puente Yale", "228"), ("Puente Víctor Raúl", "***"), ("PTZ Poste 10 Plazuela Pescador", "***"),
            ("Posta Cono Norte", "202"), ("Pollería Maruja", "225"), ("Politécnico", "207"), ("Plazuela Pescador", "204"),
            ("Plazuela Cáceres", "230"), ("Pecata", "226"), ("Parcela 25", "201"), ("Muelle Uno", "212"),
            ("Mercado Acapulco", "210"), ("Max Cornejo Pacora", "205"), ("Malecón San Pedro", "206"), ("Intercom Primax", "MARCAR EL 5"),
            ("Intercom Plazuela Pescador", "MARCAR EL 10"), ("Grifo Primax", "229"), ("Grifo Acapulco", "209"),
            ("Estadio Campeonísimo", "231"), ("Es Salud", "208"), ("Cocobongo", "211"), ("Camara PTZ Poste Primax", "***"),
            ("Base Cono Norte", "203"), ("FONAVI", "241"), ("Coliseo los Pinos", "243"), ("María Reina de la Paz", "242"),
            ("Ovalo Urba", "246"), ("Iglesia Señor de los Milagros", "247"), ("Calle 01 Talara Alta", "248"), ("SAPISA", "249"),
            ("Parque 28 Julio", "250"), ("Tanque Víctor Raúl", "252"), ("Posta Quiñones", "254"), ("Plazuela Quiñones", "256"),
            ("Colegio Señor de los Milagros", "257"), ("Escuela de San Sebastián", "258"), ("Paradero 20", "253"),
            ("Colegio 13", "255"), ("Cola de Gato", "263"), ("Cuadrado del Agua", "260"), ("Gruta Jorge Chávez", "259"),
            ("Pilar Nores", "261"), ("Chatarreros", "262"), ("Mario Aguirre", "264"), ("CORPAC", "244"), ("07 de Junio", "251"),
            ("PTZ Poste Ovalo de la Urba", "***"), ("Intercom Óvalo Urba", "MARCAR EL 1"), ("Poste 06 Gruta Jorge Chávez", "***"),
            ("Intercom Gruta Jorge Chávez", "MARCAR EL 6"), ("Poste 07 Aeropuerto", "***"), ("Aeropuerto", "MARCAR EL 7"),
            ("Poste 09 Víctor Raúl", "***"), ("Intercom Víctor Raúl", "MARCAR EL 9"),
            # Nuevos ingresos
            ("Sacobsa", "265"),
            ("Grifo Challe N.T", "266"),
            ("Negreiros-Luciano", "267"),
            ("Tanque Elevado", "268"),
            ("Enace II Antena", "269")
        ]
        return sorted([item for item in raw_data if len(item) == 2], key=lambda x: x[0].lower())

    def _setup_window(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("🔊 Buscador de Megáfonos")
        self.window.geometry("600x750")
        self.window.resizable(False, False)
        self.window.attributes('-topmost', True)
        self.window.configure(bg="#f8f9fa")
        self.window.protocol("WM_DELETE_WINDOW", lambda: None)
        self.window.bind('<Escape>', lambda e: self._on_close())

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.colors = {
            'primary': '#2c3e50', 'secondary': '#3498db', 'accent': '#e74c3c', 'success': '#27ae60',
            'background': '#f8f9fa', 'surface': '#ffffff', 'text_primary': '#2c3e50', 'text_secondary': '#7f8c8d'
        }
        self.fonts = {
            'title': ("Segoe UI", 16, "bold"), 'subtitle': ("Segoe UI", 12, "bold"),
            'body': ("Segoe UI", 10), 'small': ("Segoe UI", 9)
        }
        self.style.configure('Primary.TButton', font=self.fonts['subtitle'], padding=(15, 8), background=self.colors['secondary'], foreground='white')
        self.style.map('Primary.TButton', background=[('active', '#2980b9'), ('pressed', '#1f6391')])
        self.style.configure('Action.TButton', font=self.fonts['body'], padding=(10, 5), background=self.colors['success'], foreground='white')
        self.style.map('Action.TButton', background=[('active', '#219a52'), ('pressed', '#1e8449')])
        self.style.configure('Secondary.TButton', font=self.fonts['small'], padding=(5, 3), background=self.colors['accent'], foreground='white')
        self.style.map('Secondary.TButton', background=[('active', '#c0392b'), ('pressed', '#a93226')])
        self.style.configure('Search.TEntry', font=self.fonts['body'], fieldbackground=self.colors['surface'], bordercolor=self.colors['secondary'], lightcolor=self.colors['secondary'], darkcolor=self.colors['secondary'], borderwidth=2, relief='flat')

    def _create_interface(self):
        self.main_frame = tk.Frame(self.window, bg=self.colors['background'])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        self._create_header()
        self._create_search_section()
        self._create_results_section()
        self._create_actions_section()
        self._create_status_bar()

    def _create_header(self):
        header_frame = tk.Frame(self.main_frame, bg=self.colors['primary'], height=60)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Contenedor principal para imagen y textos
        content_frame = tk.Frame(header_frame, bg=self.colors['primary'])
        content_frame.pack(expand=True, fill=tk.BOTH, padx=(60, 15), pady=3)
        
        # Cargar y mostrar la imagen
        try:
            image_path = os.path.join("help", "Megafonos.png")
            if os.path.exists(image_path):
                # Cargar imagen y redimensionar a 100x100
                original_image = Image.open(image_path)
                resized_image = original_image.resize((100, 100), Image.Resampling.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(resized_image)
                
                # Frame para la imagen
                image_frame = tk.Frame(content_frame, bg=self.colors['primary'])
                image_frame.pack(side=tk.LEFT, padx=(0, 5))
                
                logo_label = tk.Label(image_frame, image=self.logo_image, bg=self.colors['primary'])
                logo_label.pack()
            else:
                # Si no existe la imagen, crear un placeholder
                image_frame = tk.Frame(content_frame, bg=self.colors['primary'], width=100, height=100)
                image_frame.pack(side=tk.LEFT, padx=(0, 5))
                image_frame.pack_propagate(False)
        except Exception as e:
            # En caso de error, crear un placeholder
            image_frame = tk.Frame(content_frame, bg=self.colors['primary'], width=100, height=100)
            image_frame.pack(side=tk.LEFT, padx=(0, 5))
            image_frame.pack_propagate(False)
        
        # Frame para los textos
        text_frame = tk.Frame(content_frame, bg=self.colors['primary'])
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Título principal
        title_label = tk.Label(text_frame, text="BUSCADOR DE MEGÁFONOS", 
                              font=self.fonts['title'], bg=self.colors['primary'], fg='white')
        title_label.pack(anchor=tk.W, pady=(0, 0))
        
        # Subtítulo
        subtitle_label = tk.Label(text_frame, text="Búsqueda inteligente • Navegación con teclado • Copia rápida", 
                                 font=self.fonts['small'], bg=self.colors['primary'], fg='#bdc3c7')
        subtitle_label.pack(anchor=tk.W, pady=(0, 0))
        
        # Instrucción
        instruction_label = tk.Label(text_frame, text="💡 Presiona ESC para cerrar la ventana", 
                                    font=self.fonts['small'], bg=self.colors['primary'], fg='#FFD700')
        instruction_label.pack(anchor=tk.W)

    def _create_search_section(self):
        search_frame = tk.LabelFrame(self.main_frame, text="🔍 Búsqueda Inteligente", font=self.fonts['subtitle'], bg=self.colors['background'], fg=self.colors['text_primary'], padx=10, pady=10)
        search_frame.pack(fill=tk.X, pady=(0, 15))
        input_frame = tk.Frame(search_frame, bg=self.colors['background'])
        input_frame.pack(fill=tk.X, pady=(0, 10))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(input_frame, textvariable=self.search_var, style='Search.TEntry', width=40)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.clear_btn = ttk.Button(input_frame, text="✖", command=self._clear_search, style='Secondary.TButton', width=3)
        self.clear_btn.pack(side=tk.RIGHT)
        tk.Label(search_frame, text="💡 Busca por nombre o código • Usa ↑↓ para navegar • Enter para seleccionar • Ctrl+C para copiar", font=self.fonts['small'], bg=self.colors['background'], fg=self.colors['text_secondary'], wraplength=550, justify=tk.LEFT).pack(anchor=tk.W)

    def _create_results_section(self):
        results_frame = tk.LabelFrame(self.main_frame, text="📋 Resultados", font=self.fonts['subtitle'], bg=self.colors['background'], fg=self.colors['text_primary'], padx=10, pady=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        scrollbar = ttk.Scrollbar(results_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_listbox = tk.Listbox(results_frame, font=self.fonts['body'], bg=self.colors['surface'], fg=self.colors['text_primary'], selectbackground=self.colors['secondary'], selectforeground='white', activestyle='none', borderwidth=0, highlightthickness=1, highlightcolor=self.colors['secondary'], yscrollcommand=scrollbar.set)
        self.results_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.results_listbox.yview)

    def _create_actions_section(self):
        actions_frame = tk.Frame(self.main_frame, bg=self.colors['background'])
        actions_frame.pack(fill=tk.X, pady=(0, 10))
        selected_frame = tk.LabelFrame(actions_frame, text="📍 Código Seleccionado", font=self.fonts['body'], bg=self.colors['background'], fg=self.colors['text_primary'], padx=10, pady=5)
        selected_frame.pack(fill=tk.X, pady=(0, 10))
        self.selected_var = tk.StringVar(value="Ninguno seleccionado")
        tk.Label(selected_frame, textvariable=self.selected_var, font=self.fonts['subtitle'], bg=self.colors['background'], fg=self.colors['secondary']).pack()
        buttons_frame = tk.Frame(actions_frame, bg=self.colors['background'])
        buttons_frame.pack()
        ttk.Button(buttons_frame, text="🔄 Limpiar Todo", command=self._reset_search, style='Action.TButton', width=15).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="❎ Cerrar", command=self._on_close, style='Secondary.TButton', width=15).pack(side=tk.LEFT)

    def _create_status_bar(self):
        self.status_bar = tk.Frame(self.window, bg=self.colors['primary'], height=25)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        # Total a la izquierda
        self.status_var = tk.StringVar(value=f"📊 Total: {len(self.data)} ubicaciones")
        self.status_label = tk.Label(self.status_bar, textvariable=self.status_var, font=self.fonts['small'], bg=self.colors['primary'], fg='white')
        self.status_label.pack(side=tk.LEFT, padx=5)
        # Operador a la derecha
        operador = platform.node().upper()
        self.operador_label = tk.Label(self.status_bar, text=f"🪪 Usuario: {operador}", font=self.fonts['small'], bg=self.colors['primary'], fg='white')
        self.operador_label.pack(side=tk.RIGHT, padx=5)

    def _setup_bindings(self):
        self.search_var.trace_add('write', self._on_search_change)
        self.search_entry.bind('<Return>', self._on_search_enter)
        self.search_entry.bind('<Down>', self._focus_results)
        self.search_entry.bind('<Control-a>', self._select_all_search)
        self.results_listbox.bind('<<ListboxSelect>>', self._on_result_select)
        self.results_listbox.bind('<Return>', self._on_result_enter)
        self.results_listbox.bind('<Double-Button-1>', self._copy_to_clipboard)
        self.window.bind('<Control-c>', self._copy_to_clipboard)
        self.window.bind('<Control-f>', lambda e: self.search_entry.focus_set())
        self.window.bind('<F5>', lambda e: self._reset_search())
        self._setup_navigation_keys()
        self.search_entry.focus_set()
        self._update_results()

    def _setup_navigation_keys(self):
        def navigate_results(direction):
            current = self.results_listbox.curselection()
            size = self.results_listbox.size()
            if size == 0:
                return
            new_index = 0 if not current else min(max(current[0] + (1 if direction == 'down' else -1), 0), size - 1)
            self.results_listbox.selection_clear(0, tk.END)
            self.results_listbox.selection_set(new_index)
            self.results_listbox.see(new_index)
            self._on_result_select(None)
        for widget in [self.search_entry, self.results_listbox]:
            widget.bind('<Up>', lambda e: navigate_results('up'))
            widget.bind('<Down>', lambda e: navigate_results('down'))

    def _on_search_change(self, *args):
        self._update_results()

    def _update_results(self):
        search_text = self.search_var.get().strip()
        self.filtered_data = self.data if not search_text else self._smart_search(search_text)
        self.results_listbox.delete(0, tk.END)
        
        # Find the maximum length of location names for proper alignment
        max_name_length = max(len(nombre) for nombre, _ in self.filtered_data) if self.filtered_data else 0
        
        for nombre, codigo in self.filtered_data:
            # Format with fixed width and proper alignment
            formatted_line = f"📍 {nombre:<{max_name_length}} 🔊 {codigo}"
            self.results_listbox.insert(tk.END, formatted_line)
            
        self._update_status()
        if search_text and self.filtered_data:
            self.results_listbox.selection_set(0)
            self._on_result_select(None)

    def _smart_search(self, query):
        query = query.lower()
        results = []
        for condition in [
            lambda x: x[1].lower() == query,
            lambda x: x[1].lower().startswith(query),
            lambda x: x[0].lower().startswith(query),
            lambda x: query in x[1].lower(),
            lambda x: query in x[0].lower()
        ]:
            results.extend([item for item in self.data if condition(item) and item not in results])
        if ' ' in query:
            query_words = query.split()
            results.extend([item for item in self.data if all(word in item[0].lower() for word in query_words) and item not in results])
        return results

    def _on_search_enter(self, event):
        if self.filtered_data:
            self.results_listbox.selection_set(0)
            self.results_listbox.focus_set()
            self._on_result_select(None)

    def _focus_results(self, event):
        if self.results_listbox.size() > 0:
            self.results_listbox.focus_set()
            if not self.results_listbox.curselection():
                self.results_listbox.selection_set(0)
                self._on_result_select(None)

    def _on_result_select(self, event):
        selection = self.results_listbox.curselection()
        if selection and self.filtered_data:
            index = selection[0]
            if 0 <= index < len(self.filtered_data):
                nombre, codigo = self.filtered_data[index]
                self.selected_var.set(f"{codigo} - {nombre}")
                self.current_selection = index

    def _on_result_enter(self, event):
        self._copy_to_clipboard()

    def _select_all_search(self, event):
        self.search_entry.select_range(0, tk.END)
        return 'break'

    def _copy_to_clipboard(self, event=None):
        if 0 <= self.current_selection < len(self.filtered_data):
            nombre, codigo = self.filtered_data[self.current_selection]
            self.window.clipboard_clear()
            self.window.clipboard_append(codigo)
            self._show_copy_feedback(codigo, nombre)

    def _show_copy_feedback(self, codigo, nombre):
        pass

    def _clear_search(self):
        self.search_var.set("")
        self.search_entry.focus_set()

    def _reset_search(self):
        self.search_var.set("")
        self.selected_var.set("Ninguno seleccionado")
        self.results_listbox.selection_clear(0, tk.END)
        self.current_selection = -1
        self.search_entry.focus_set()
        self._update_results()

    def _update_status(self):
        total = len(self.data)
        filtered = len(self.filtered_data)
        self.status_var.set(f"📊 Total: {total} ubicaciones" if filtered == total else f"📊 Mostrando: {filtered} de {total} ubicaciones")

    def _keep_on_top(self):
        self.window.attributes('-topmost', True)
        self.window.after(1000, self._check_topmost)

    def _check_topmost(self):
        if self.window.winfo_exists() and not self.window.attributes('-topmost'):
            self.window.attributes('-topmost', True)
        self.window.after(1000, self._check_topmost)

    def _on_close(self):
        MegafonosWindow._window_open = False
        self.window.destroy()

def abrir_ventana_megafonos(parent):
    MegafonosWindow(parent)

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = MegafonosWindow(root)
    root.mainloop()