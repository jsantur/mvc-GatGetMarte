# view.py (versión OPTIMIZADA - Interfaz Moderna y Responsiva)
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import json
import os
from report_ocurrencias import abrir_ventana_ocurrencias  # Nueva importación
import time
import webbrowser


class View:
    def __init__(self, root):
        self.root = root
        self.controller = None
        
        # COLORES MODERNOS - Esquema mejorado
        self.COLOR_FONDO = "#f8f9fa"
        self.COLOR_HEADER = "#2c3e50"
        self.COLOR_ACCENT = "#3498db"
        self.COLOR_SUCCESS = "#27ae60"
        self.COLOR_WARNING = "#f39c12"
        self.COLOR_DANGER = "#e74c3c"
        
        # Variables para navegación por filas
        self.navigation_mode = False  # Modo de navegación activo/inactivo
        self.current_highlighted_row = -1  # Índice de la fila actualmente resaltada (-1 = ninguna)
        self.HIGHLIGHT_COLOR = "#FFECB3"  # Celeste medio con buena visibilidad. para el resaltado
        
        self.child_windows = []  # Lista para rastrear ventanas secundarias
        
        # Cargar iconos para las pestañas del Notebook
        try:
            from PIL import Image, ImageTk
            icon_km = Image.open(os.path.join("help", "km.png")).resize((24, 24), Image.Resampling.LANCZOS)
            self.icon_tab_km = ImageTk.PhotoImage(icon_km)
        except Exception:
            self.icon_tab_km = None

        # CONFIGURACIÓN PANTALLA COMPLETA Y MODERNA
        self.root.title("🛰️ SERENAZGO - SISTEMA DE MONITOREO AVANZADO")
        self.root.state('zoomed')  # Pantalla completa en Windows
        self.root.configure(bg=self.COLOR_FONDO)
        self.root.resizable(True, True)  # Permitir redimensión
        self.root.attributes('-topmost', True)

        # FUENTES MEJORADAS - MÁS LEGIBLES
        self.configurar_fuentes()

        # Variables de control
        self.filtro_var = tk.StringVar(value="TODAS")
        self.turno_var = tk.StringVar()
        self.reloj_var = tk.StringVar()
        self.contador_pickup = tk.StringVar(value="Pick-ups seleccionadas: 0/8")
        self.contador_autos = tk.StringVar(value="Autos Sedán seleccionados: 0/3")
        self.resumen_var = tk.StringVar()
        self.busqueda_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Estado: Sistema listo para operar")

        self.fila_widgets_data = [] # Para almacenar referencias a los widgets de cada fila
        self.unidades_mostradas = [] # Para controlar qué unidades se muestran actualmente
        
        # Variables de control para ordenamiento
        self.sort_column = None  # Columna actualmente ordenada
        self.sort_ascending = True  # Dirección del ordenamiento
        self.sort_buttons = {}  # Diccionario para almacenar los botones de ordenamiento

    def configurar_fuentes(self):
        """Configura fuentes más grandes y legibles para toda la aplicación."""
        # FUENTES PRINCIPALES - AUMENTADAS PARA MEJOR LEGIBILIDAD
        self.font_titulo = ("Segoe UI", 18, "bold")        # Era 14
        self.font_subtitulo = ("Segoe UI", 14, "bold")     # Era 12
        self.font_base = ("Segoe UI", 12)                  # Era 10
        self.font_boton = ("Segoe UI", 12, "bold")         # Era 10
        self.font_tabla = ("Segoe UI", 11, "bold")         # Era 9
        self.font_status = ("Segoe UI", 11)                # Era 9
        
        # Configurar fuentes por defecto para toda la aplicación
        self.root.option_add("*Font", self.font_base)
        self.root.option_add("*Button.Font", self.font_boton)
        self.root.option_add("*Label.Font", self.font_base)
        self.root.option_add("*Entry.Font", self.font_base)

    def toggle_navigation_mode(self):
        """Activa o desactiva el modo de navegación por filas."""
        self.navigation_mode = not self.navigation_mode
        if self.navigation_mode:
            # Activar modo de navegación
            self.current_highlighted_row = 0  # Comenzar en la primera fila
            self.highlight_current_row()
            self.update_status("Modo navegación activo - Presiona Enter para navegar, Escape para salir", "blue")
        else:
            # Desactivar modo de navegación
            self.clear_navigation_highlight()
            self.current_highlighted_row = -1
            self.update_status("Modo navegación desactivado", "green")

    def highlight_current_row(self):
        """Resalta la fila actual con color amarillo."""
        if not self.navigation_mode or self.current_highlighted_row < 0:
            return
            
        # Obtener las filas visibles
        visible_rows = [fila for fila in self.fila_widgets_data if fila['lbl_unidad'].winfo_viewable()]
        
        if not visible_rows:
            return
            
        # Asegurar que el índice esté dentro del rango
        if self.current_highlighted_row >= len(visible_rows):
            self.current_highlighted_row = 0
        elif self.current_highlighted_row < 0:
            self.current_highlighted_row = len(visible_rows) - 1
            
        # Limpiar resaltado anterior
        self.clear_navigation_highlight()
        
        # Resaltar la fila actual
        current_fila = visible_rows[self.current_highlighted_row]
        self.apply_navigation_highlight(current_fila)
        
        # Hacer scroll para mostrar la fila si es necesario
        self.scroll_to_row(current_fila)

    def clear_navigation_highlight(self):
        """Limpia el resaltado de navegación de todas las filas."""
        for fila_data in self.fila_widgets_data:
            self.remove_navigation_highlight(fila_data)

    def apply_navigation_highlight(self, fila_data):
        """Aplica el resaltado amarillo a una fila específica."""
        widgets_to_highlight = [
            fila_data['chk_widget'],
            fila_data['lbl_unidad'],
            fila_data['entry_km'],
            fila_data['entry_ap'],
            fila_data['entry_po'],
            fila_data['turnos_frame'],
            fila_data['lbl_obs_km'],
            fila_data['lbl_obs_ap'],
            fila_data['lbl_obs_po']
        ]
        
        for widget in widgets_to_highlight:
            try:
                if isinstance(widget, tk.Checkbutton):
                    widget.config(bg=self.HIGHLIGHT_COLOR, activebackground=self.HIGHLIGHT_COLOR)
                elif isinstance(widget, tk.Entry):
                    widget.config(bg=self.HIGHLIGHT_COLOR, disabledbackground=self.HIGHLIGHT_COLOR)
                elif isinstance(widget, tk.Frame):
                    widget.config(bg=self.HIGHLIGHT_COLOR)
                    # Actualizar el fondo de los checkboxes dentro del frame
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Checkbutton):
                            child.config(bg=self.HIGHLIGHT_COLOR, activebackground=self.HIGHLIGHT_COLOR)
                else:
                    widget.config(bg=self.HIGHLIGHT_COLOR)
            except tk.TclError:
                pass  # Ignorar errores con widgets que no soportan cambio de color

    def remove_navigation_highlight(self, fila_data):
        """Remueve el resaltado amarillo de una fila específica y restaura el resaltado original."""
        # Primero remover el resaltado amarillo
        widgets_to_restore = [
            fila_data['chk_widget'],
            fila_data['lbl_unidad'],
            fila_data['entry_km'],
            fila_data['entry_ap'],
            fila_data['entry_po'],
            fila_data['turnos_frame'],
            fila_data['lbl_obs_km'],
            fila_data['lbl_obs_ap'],
            fila_data['lbl_obs_po']
        ]
        
        for widget in widgets_to_restore:
            try:
                if isinstance(widget, tk.Checkbutton):
                    widget.config(bg="white", activebackground="white")
                elif isinstance(widget, tk.Entry):
                    widget.config(bg="white", disabledbackground="white")
                elif isinstance(widget, tk.Frame):
                    widget.config(bg="white")
                    # Restaurar el fondo de los checkboxes dentro del frame
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Checkbutton):
                            child.config(bg="white", activebackground="white")
                else:
                    widget.config(bg="white")
            except tk.TclError:
                pass
        
        # Luego aplicar el resaltado original (basado en validaciones)
        self.update_row_highlighting(fila_data)

    def scroll_to_row(self, fila_data):
        """Hace scroll para mostrar la fila resaltada."""
        try:
            # Obtener la posición Y de la fila
            y_position = fila_data['lbl_unidad'].winfo_y()
            
            # Calcular la posición del canvas para centrar la fila
            canvas_height = self.canvas.winfo_height()
            row_height = fila_data['lbl_unidad'].winfo_height()
            
            # Calcular la posición objetivo para centrar la fila
            target_y = y_position - (canvas_height // 2) + (row_height // 2)
            
            # Asegurar que no sea negativo
            target_y = max(0, target_y)
            
            # Hacer scroll
            self.canvas.yview_moveto(target_y / self.scrollable_frame.winfo_height())
        except Exception:
            pass  # Ignorar errores de scroll

    def navigate_to_next_row(self):
        """Navega a la siguiente fila."""
        if not self.navigation_mode:
            return
            
        # Obtener las filas visibles
        visible_rows = [fila for fila in self.fila_widgets_data if fila['lbl_unidad'].winfo_viewable()]
        
        if not visible_rows:
            return
            
        # Mover al siguiente índice
        self.current_highlighted_row += 1
        
        # Si llegamos al final, volver al principio
        if self.current_highlighted_row >= len(visible_rows):
            self.current_highlighted_row = 0
            
        # Aplicar el resaltado
        self.highlight_current_row()

    def navigate_to_previous_row(self):
        """Navega a la fila anterior."""
        if not self.navigation_mode:
            return
            
        # Obtener las filas visibles
        visible_rows = [fila for fila in self.fila_widgets_data if fila['lbl_unidad'].winfo_viewable()]
        
        if not visible_rows:
            return
            
        # Mover al índice anterior
        self.current_highlighted_row -= 1
        
        # Si llegamos al principio, ir al final
        if self.current_highlighted_row < 0:
            self.current_highlighted_row = len(visible_rows) - 1
            
        # Aplicar el resaltado
        self.highlight_current_row()

    def get_selected_units(self):
        """Retorna una lista de aliases de las unidades seleccionadas en la vista principal."""
        return [fila['alias'] for fila in self.fila_widgets_data 
                if fila['var_chk'].get() and fila['alias'] in self.unidades_mostradas]

    def register_child_window(self, window):
        """Registra una ventana secundaria para cerrarla cuando la principal se cierre."""
        self.child_windows.append(window)

    def close_all_child_windows(self):
        """Cierra todas las ventanas secundarias registradas."""
        while self.child_windows:
            window = self.child_windows.pop(0)  # Usar pop para evitar problemas de iteración
            if window.winfo_exists():
                try:
                    print(f"Cerrando ventana secundaria: {window}")
                    window.destroy()
                except Exception as e:
                    print(f"Error cerrando ventana: {e}")
        print("Todas las ventanas secundarias cerradas")

    def set_controller(self, controller):
        self.controller = controller
        self.create_widgets() # Now it's safe to create widgets and bind commands
        self.setup_menu() # Setup menu here as well
        self.configurar_atajos_avanzados()  # Configurar atajos sensibles a mayúsculas
        
    def configurar_atajos_avanzados(self):
        """Configura atajos de teclado sensibles a mayúsculas/minúsculas y funcionales con Bloq Mayús."""
        def atajo_control(event):
            if not self.controller:
                return
            # Normalizar la tecla ignorando Bloq Mayús
            key = event.keysym
            is_shift = (event.state & 0x1) != 0 or (event.state & 0x0001) != 0  # Shift puede ser 0x1 o 0x0001
            key_lower = key.lower()
            
            # ATAJOS DE ORDENAMIENTO (Ctrl + número) - PRIORIDAD ALTA
            if key in ['1', '2', '3']:
                column_map = {'1': 1, '2': 2, '3': 3}
                self.toggle_sort(column_map[key])
                return
            
            # ATAJOS BÁSICOS (Ctrl + letra minúscula, sin Shift)
            if not is_shift:
                if key_lower == 'm':
                    self.controller.megafono()
                elif key_lower == 'p':
                    self.controller.imprimir_reporte()
                elif key_lower == 'q':
                    self.controller.confirmar_salida()
                elif key_lower == 's':
                    if self.btn_guardar['state'] == tk.NORMAL:
                        self.controller.guardar_datos()
                elif key_lower == 'f':
                    self.search_entry.focus_set()
                elif key_lower == 'r':
                    self.reset_sorting_on_filter_change()  # Ctrl+R para resetear ordenamiento
            # ATAJOS AVANZADOS (Ctrl+Shift+letra)
            else:
                if key_lower == 'm':
                    self.controller.open_sipcop()
                elif key_lower == 'p':
                    self.abrir_reporte_unidades()
                elif key_lower == 'q':
                    self.close_all_child_windows()
                elif key_lower == 's':
                    if self.btn_capturar['state'] == tk.NORMAL:
                        self.controller.capturar_pantalla_completa()
                elif key_lower == 'g':
                    self.controller.open_wialon()
                elif key_lower == 'v':
                    self.controller.open_visor_tactico()
                elif key_lower == 'r':
                    self.controller.force_time_update()
                elif key_lower == 'b':
                    self.abrir_backup_bd()
        # Un solo binding para todos los atajos Ctrl
        self.root.bind_all('<Control-KeyPress>', atajo_control)
        # Atajos especiales fuera de Ctrl
        self.root.bind('<F1>', lambda e: self.mostrar_ayuda_atajos())
        self.root.bind('<F2>', lambda e: self.mostrar_manual_usuario())
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
        # Los Alt y otros atajos se mantienen igual (ya están en otros métodos)

    def mostrar_ayuda_atajos(self):
        """Muestra una ventana con la lista de atajos disponibles."""
        ayuda_window = tk.Toplevel(self.root)
        ayuda_window.title("🔧 Atajos de Teclado - Guía Rápida")
        ayuda_window.geometry("600x650")
        ayuda_window.configure(bg=self.COLOR_FONDO)
        ayuda_window.attributes('-topmost', True)
        ayuda_window.protocol("WM_DELETE_WINDOW", lambda: ayuda_window.destroy())
        ayuda_window.bind('<Escape>', lambda e: ayuda_window.destroy())
        
        main_frame = tk.Frame(ayuda_window, bg=self.COLOR_FONDO)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="🔧 ATAJOS DE TECLADO DISPONIBLES", 
                font=self.font_titulo, bg=self.COLOR_FONDO, fg=self.COLOR_HEADER).pack(pady=(0, 20))
        
        atajos_text = """
 🎯 NAVEGACION Y TABLA:
 - Enter -> Activar modo navegacion / Siguiente fila
 - Escape -> Desactivar modo navegacion / Salir
 - Ctrl + 1 / 2 / 3 -> Ordenar por Unidad, KM o AP
 - Ctrl + R -> Resetear ordenamiento
 
 ✏️ ACCIONES RAPIDAS (Alt + tecla):
 - Alt + E -> MODO EDICION (Obligatorio para guardar)
 - Alt + G -> GUARDAR DATOS (Local y Nube)
 - Alt + C -> LISTA DE CAMARAS (Nuevo panel)
 - Alt + U -> ULTIMO REGISTRO (Sincronizar Cloud)
 - Alt + L -> LIMPIAR FORMULARIO
 - Alt + O -> ABRIR OCURRENCIAS
 - Alt + B -> ENFOCAR BUSQUEDA
 - Alt + D -> VACIAR BD (¡Cuidado!)
 
 📋 SISTEMA (Ctrl + Shift + tecla):
 - Ctrl + Shift + P -> Reporte de Unidades
 - Ctrl + Shift + B -> Abrir BACKUP EXCEL
 - Ctrl + Shift + S -> CAPTURAR PANTALLA
 - Ctrl + Shift + G -> Abrir Wialon
 - Ctrl + Shift + M -> Abrir SIPCOP-M
 - Ctrl + Shift + R -> Actualizar Hora NTP
 
 ⌨️ TECLAS DE FUNCION:
 - F1 -> Mostrar esta Ayuda
 - F2 -> Manual de Usuario (Markdown)
 - F5 -> Actualizar Vista
 - F11 -> Pantalla Completa
 
 📧 OTROS:
 - Ctrl + J -> Contacto del Desarrollador
 - Ctrl + Q -> Salir de la Aplicacion
        """
        text_widget = tk.Text(main_frame, wrap=tk.WORD, font=self.font_base,
                             bg="white", fg=self.COLOR_HEADER, relief=tk.SOLID, bd=1)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, atajos_text)
        text_widget.config(state=tk.DISABLED)
        ttk.Button(main_frame, text="Cerrar", 
                  command=ayuda_window.destroy).pack(pady=(10, 0))
        self.register_child_window(ayuda_window)
        
    def mostrar_manual_usuario(self):
        """Muestra el manual de usuario en una ventana con formato markdown."""
        manual_window = tk.Toplevel(self.root)
        manual_window.title("📚 Manual de Usuario - Sistema de Control de Unidades")
        manual_window.geometry("900x700")
        manual_window.configure(bg=self.COLOR_FONDO)
        manual_window.attributes('-topmost', True)
        
        # Centrar la ventana
        manual_window.transient(self.root)
        manual_window.grab_set()
        
        # Frame principal
        main_frame = tk.Frame(manual_window, bg=self.COLOR_FONDO)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(main_frame, text="📚 MANUAL DE USUARIO", 
                              font=('Segoe UI', 16, 'bold'), 
                              bg=self.COLOR_FONDO, fg=self.COLOR_HEADER)
        title_label.pack(pady=(0, 20))
        
        # Frame para el contenido con scroll
        content_frame = tk.Frame(main_frame, bg=self.COLOR_FONDO)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear Text widget con scrollbar
        text_frame = tk.Frame(content_frame, bg=self.COLOR_FONDO)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Text widget
        text_widget = tk.Text(text_frame, wrap=tk.WORD, 
                             font=('Segoe UI', 10),
                             bg='white', fg='#2c3e50',
                             relief=tk.SOLID, bd=1,
                             yscrollcommand=scrollbar.set)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=text_widget.yview)
        
        # Cargar contenido del manual
        try:
            manual_path = "manual_usuario.md"
            if os.path.exists(manual_path):
                with open(manual_path, 'r', encoding='utf-8') as file:
                    manual_content = file.read()
            else:
                # Contenido embebido como fallback
                manual_content = self.get_manual_content_embebido()
            
            # Insertar contenido con formato básico
            text_widget.insert(tk.END, manual_content)
            
            # Aplicar formato básico (títulos en negrita)
            self.apply_basic_formatting(text_widget)
            
        except Exception as e:
            text_widget.insert(tk.END, f"Error al cargar el manual: {str(e)}\n\n")
            text_widget.insert(tk.END, self.get_manual_content_embebido())
        
        # Configurar el text widget como solo lectura
        text_widget.config(state=tk.DISABLED)
        
        # Botones de acción
        button_frame = tk.Frame(main_frame, bg=self.COLOR_FONDO)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Botón para abrir el archivo manual
        def abrir_manual_externo():
            try:
                import subprocess
                import platform
                
                manual_path = "manual_usuario.md"
                if not os.path.exists(manual_path):
                    messagebox.showerror("Error", "No se encontró el archivo manual_usuario.md")
                    return
                
                if platform.system() == "Windows":
                    os.startfile(manual_path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", manual_path])
                else:  # Linux
                    subprocess.run(["xdg-open", manual_path])
                    
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el archivo: {str(e)}")
        
        ttk.Button(button_frame, text="📄 Abrir en Editor", 
                  command=abrir_manual_externo).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Cerrar", 
                  command=manual_window.destroy).pack(side=tk.RIGHT)
        
        # Atajos de teclado
        manual_window.bind('<Escape>', lambda e: manual_window.destroy())
        manual_window.bind('<F2>', lambda e: manual_window.destroy())
        
        # Centrar la ventana
        manual_window.update_idletasks()
        x = (manual_window.winfo_screenwidth() // 2) - (manual_window.winfo_width() // 2)
        y = (manual_window.winfo_screenheight() // 2) - (manual_window.winfo_height() // 2)
        manual_window.geometry(f"+{x}+{y}")
        
        self.register_child_window(manual_window)
        
    def get_manual_content_embebido(self):
        """Retorna el contenido del manual embebido como texto."""
        return """# 📚 Manual de Usuario - Sistema de Control de Unidades (v2.1)

## 1. Introducción
Este sistema gestiona unidades de serenazgo en Talara con guardado local y en la nube.

### Novedades v2.1:
- Sincronización Cloud (Google Sheets).
- Panel de Cámaras (Alt+C) con autocompletado e historial.
- Control de Jurisdicción y multi-turno individual por unidad.

## 2. Registro de Datos
- Use Alt+E para activar el modo EDICIÓN.
- Use Alt+G para GUARDAR (Local y Nube).
- Use Alt+B para enfocar la barra de búsqueda rápida.

## 3. Gestión de Cámaras (Alt+C)
- El panel permite buscar cámaras oficiales por nombre y generar reportes con un solo clic.

---
Manual actualizado al 05 de Abril de 2026."""

    def apply_basic_formatting(self, text_widget):
        """Aplica formato básico al texto del manual."""
        content = text_widget.get("1.0", tk.END)
        
        # Configurar tags para diferentes estilos
        text_widget.tag_configure("title", font=('Segoe UI', 14, 'bold'), foreground='#2c3e50')
        text_widget.tag_configure("subtitle", font=('Segoe UI', 12, 'bold'), foreground='#34495e')
        text_widget.tag_configure("section", font=('Segoe UI', 11, 'bold'), foreground='#2980b9')
        text_widget.tag_configure("emphasis", font=('Segoe UI', 10, 'bold'), foreground='#e74c3c')
        text_widget.tag_configure("code", font=('Consolas', 9), background='#f8f9fa', foreground='#495057')
        
        # Aplicar formato a títulos principales
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('# '):
                start = f"{i+1}.0"
                end = f"{i+1}.end"
                text_widget.tag_add("title", start, end)
            elif line.startswith('## '):
                start = f"{i+1}.0"
                end = f"{i+1}.end"
                text_widget.tag_add("subtitle", start, end)
            elif line.startswith('### '):
                start = f"{i+1}.0"
                end = f"{i+1}.end"
                text_widget.tag_add("section", start, end)
            elif line.startswith('- **') or line.startswith('• **'):
                start = f"{i+1}.0"
                end = f"{i+1}.end"
                text_widget.tag_add("emphasis", start, end)
        
    def toggle_fullscreen(self):
        """Alterna entre pantalla completa y ventana normal."""
        current_state = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current_state)
        if not current_state:
            self.root.attributes('-topmost', True)
    
    def setup_menu(self):
        """Configura la barra de menú superior con mejor organización."""
        if not self.controller: # Safety check, though it should be set by now
            return
        
        menubar = tk.Menu(self.root, font=self.font_base)
        self.root.config(menu=menubar)

        # MENÚ PRINCIPAL REORGANIZADO
        menu_principal = tk.Menu(menubar, tearoff=0, font=self.font_base)
        menubar.add_cascade(label="📋 SISTEMA", menu=menu_principal)

        # Reporte de Unidades
        menu_principal.add_command(
            label="📋 Reporte de Unidades", 
            command=self.abrir_reporte_unidades,
            accelerator="Ctrl+Shift+P"
        )

        # BACKUP BD
        menu_principal.add_command(
            label="💾 BACKUP BD", 
            command=self.abrir_backup_bd,
            accelerator="Ctrl+Shift+B"
        )

        # MENÚ DE HERRAMIENTAS
        menu_herramientas = tk.Menu(menubar, tearoff=0, font=self.font_base)
        menubar.add_cascade(label="🔧 HERRAMIENTAS", menu=menu_herramientas)

        menu_herramientas.add_command(
            label="📢 Megáfono", 
            command=self.controller.megafono, 
            accelerator="Ctrl+M"
        )
        
        menu_herramientas.add_command(
            label="📝 Ocurrencias", 
            command=lambda: abrir_ventana_ocurrencias(self.root, self.turno_var.get()),
            accelerator="Alt+O"
        )
        
        menu_herramientas.add_command(
            label="📹 Lista de Cámaras", 
            command=self.abrir_lista_camaras,
            accelerator="Alt+C"
        )
        
        menu_herramientas.add_separator()
        
        menu_herramientas.add_command(
            label="🖨️ Imprimir Reporte", 
            command=self.controller.imprimir_reporte, 
            accelerator="Ctrl+P"
        )
        
        # MENÚ DE ENLACES EXTERNOS
        menu_enlaces = tk.Menu(menubar, tearoff=0, font=self.font_base)
        menubar.add_cascade(label="🌐 ENLACES", menu=menu_enlaces)
        
        menu_enlaces.add_command(
            label="📏 Cargar KM Wialon (Tiempo Real)", 
            command=self.controller.consultar_km_wialon,
            accelerator="Ctrl+G"
        )
        menu_enlaces.add_command(
            label="🌍 Wialon Web (Monitor)", 
            command=self.controller.abrir_url_wialon,
            accelerator="Ctrl+Shift+G"
        )
        
        menu_enlaces.add_command(
            label="🗺️ SIPCOP-M", 
            command=self.controller.open_sipcop,
            accelerator="Ctrl+Shift+M"
        )

        menu_enlaces.add_command(
            label="🛰️ Visor Táctico", 
            command=self.controller.open_visor_tactico,
            accelerator="Ctrl+Shift+V"
        )

        # MENÚ DE AYUDA
        menu_ayuda = tk.Menu(menubar, tearoff=0, font=self.font_base)
        menubar.add_cascade(label="❓ AYUDA", menu=menu_ayuda)
        
        menu_ayuda.add_command(
            label="🔧 Atajos de Teclado", 
            command=self.mostrar_ayuda_atajos,
            accelerator="F1"
        )
        
        # NUEVO: Manual de Usuario
        menu_ayuda.add_command(
            label="📚 Manual", 
            command=self.mostrar_manual_usuario,
            accelerator="F2"
        )
        
        # NUEVO: Contacto
        menu_ayuda.add_command(
            label="📧 Contacto", 
            command=self.controller.mostrar_contacto,
            accelerator="Ctrl+J"
        )
        
        menu_ayuda.add_separator()
        
        menu_ayuda.add_command(
            label="❌ Salir", 
            command=self.controller.confirmar_salida, 
            accelerator="Ctrl+Q"
        )

        # Vincular nuevos atajos del menú
        self.root.bind('<Alt-o>', lambda e: abrir_ventana_ocurrencias(self.root, self.turno_var.get()))
        self.root.bind('<Alt-O>', lambda e: abrir_ventana_ocurrencias(self.root, self.turno_var.get()))
        self.root.bind('<Alt-c>', lambda e: self.abrir_lista_camaras())
        self.root.bind('<Alt-C>', lambda e: self.abrir_lista_camaras())
        # Atajo global para Contacto (Ctrl+J)
        def atajo_contacto(event):
            key = event.keysym.lower()
            is_ctrl = (event.state & 0x4) != 0 or (event.state & 0x0004) != 0
            if is_ctrl and key == 'j':
                self.controller.mostrar_contacto()
        self.root.bind_all('<Control-j>', atajo_contacto, add='+')
        
        # Atajo global para BACKUP BD (Ctrl+Shift+B)
        def atajo_backup_bd(event):
            key = event.keysym.lower()
            is_ctrl = (event.state & 0x4) != 0 or (event.state & 0x0004) != 0
            is_shift = (event.state & 0x1) != 0 or (event.state & 0x0001) != 0
            if is_ctrl and is_shift and key == 'b':
                self.abrir_backup_bd()
        self.root.bind_all('<Control-B>', atajo_backup_bd, add='+')

    def abrir_reporte_unidades(self):
        """Ejecuta el script report_unidades.py en un proceso separado con los datos actuales."""
        try:
            # Obtener datos actuales del modelo
            unidades_disponibles, alias_unidades, camionetas, autos = self.controller.model.get_unit_info()
            
            # Obtener el filtro activo
            filtro_activo = self.get_filtro_var()
            
            # Obtener unidades seleccionadas manualmente si el filtro es MANUAL
            unidades_manuales = []
            if filtro_activo == 'MANUAL':
                unidades_manuales = [fila['alias'] for fila in self.fila_widgets_data 
                                if fila['var_chk'].get() and fila['alias'] in self.unidades_mostradas]
            
            # Preparar datos para pasar a la ventana
            unidades_data = {
                'unidades_disponibles': unidades_disponibles,
                'alias_unidades': alias_unidades,
                'camionetas': camionetas,
                'autos': autos,
                'turno_actual': self.get_turno_var(),
                'filtro_activo': filtro_activo,
                'unidades_manuales': unidades_manuales
            }
            
            # Importar y abrir la ventana directamente (sin subprocess)
            from report_unidades import abrir_ventana_unidades
            abrir_ventana_unidades(self.root, unidades_data)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el reporte de unidades:\\n{str(e)}")
            print(f"Error al abrir reporte: {str(e)}")  # Para depuración

    def abrir_backup_bd(self):
        """Abre el archivo Excel de backup de la base de datos."""
        try:
            import subprocess
            import platform
            
            # Ruta del archivo Excel
            excel_file = "unidades_registro.xlsx"
            
            # Verificar si el archivo existe
            if not os.path.exists(excel_file):
                messagebox.showerror("Error", f"No se encontró el archivo: {excel_file}")
                return
            
            # Abrir el archivo según el sistema operativo
            if platform.system() == "Windows":
                os.startfile(excel_file)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", excel_file])
            else:  # Linux
                subprocess.run(["xdg-open", excel_file])
                
            self.update_status(f"Archivo Excel abierto: {excel_file}", "green")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo Excel:\\n{str(e)}")
            print(f"Error al abrir Excel: {str(e)}")  # Para depuración

    def rebuild_unit_table(self):
        # Limpiar la tabla actual
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.fila_widgets_data = []
        self.unidades_mostradas = []
        
        # Volver a crear la tabla con los datos actualizados
        self.crear_encabezados_tabla()
        self.crear_filas_unidades()
        self.adjust_scroll_and_buttons()

    def crear_encabezados_tabla(self):
        """Crea los encabezados de la tabla con estilo mejorado y botones de ordenamiento."""
        headers = ["🏁 ✓", "🚦 Unidad", "🚔 KM", "📌 A.P", "📒 P.O", "🌙 TURNOS", "🗺️ ZONA", "🚔 OBS-KM", "📌 OBS-AP", "📒 OBS-P.O"]
        widths = [6, 14, 10, 10, 6, 18, 12, 25, 25, 25]  # Aumentado ancho de columnas de observaciones a 25
        
        for col, (text, width) in enumerate(zip(headers, widths)):
            # Crear frame para el encabezado
            header_frame = tk.Frame(self.scrollable_frame, bg=self.COLOR_HEADER, relief=tk.FLAT, bd=0)
            header_frame.grid(row=0, column=col, sticky="ew", padx=1, pady=1)
            
            # Configurar el peso de la columna para que se expanda
            self.scrollable_frame.grid_columnconfigure(col, weight=1)
            
            # Agregar botón de ordenamiento para las columnas específicas
            if col in [1, 2, 3]:  # Unidad, KM, A.P
                # Frame horizontal para label y botón (al costado)
                inner_frame = tk.Frame(header_frame, bg=self.COLOR_HEADER)
                inner_frame.pack(fill=tk.BOTH, expand=True)
                
                # Label del encabezado (a la izquierda)
                lbl = tk.Label(inner_frame, text=text, font=self.font_boton,
                            bg=self.COLOR_HEADER, fg="white", padx=3, pady=8,
                            relief=tk.FLAT, bd=0)
                lbl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                
                # Botón de ordenamiento (a la derecha, al costado)
                sort_btn = tk.Button(inner_frame, text="🔼", font=("Segoe UI", 10, "bold"),
                                   bg=self.COLOR_HEADER, fg="#CCCCCC", bd=0, padx=2, pady=2,
                                   relief=tk.FLAT, cursor="hand2",
                                   command=lambda c=col: self.toggle_sort(c))
                sort_btn.pack(side=tk.RIGHT, padx=(0, 2))
                
                # Agregar tooltip al botón
                tooltip_text = {
                    1: "Clic para ordenar por Unidad (H1 → H13)",
                    2: "Clic para ordenar por Kilómetros",
                    3: "Clic para ordenar por Auxilio Público"
                }
                self.create_tooltip(sort_btn, tooltip_text[col])
                
                # Guardar referencia al botón
                self.sort_buttons[col] = sort_btn
                
                # Hacer el label clickeable también
                lbl.bind("<Button-1>", lambda e, c=col: self.toggle_sort(c))
                lbl.config(cursor="hand2")
                
                # Agregar tooltip al label también
                self.create_tooltip(lbl, tooltip_text[col])
            else:
                # Para otras columnas, solo el label
                lbl = tk.Label(header_frame, text=text, font=self.font_boton,
                            bg=self.COLOR_HEADER, fg="white", padx=3, pady=8,
                            relief=tk.RAISED, bd=1)
                lbl.pack(fill=tk.BOTH, expand=True)

    def toggle_sort(self, column):
        """Alterna el ordenamiento de una columna específica."""
        if self.sort_column == column:
            # Si es la misma columna, cambiar dirección
            self.sort_ascending = not self.sort_ascending
        else:
            # Si es una columna diferente, establecer como ascendente
            self.sort_column = column
            self.sort_ascending = True
        
        # Actualizar iconos de todos los botones
        self.update_sort_icons()
        
        # Aplicar ordenamiento
        self.apply_sorting()
        
        # Actualizar estado con mensajes más descriptivos
        column_names = {1: "Unidad", 2: "KM", 3: "A.P"}
        direction = "ascendente" if self.sort_ascending else "descendente"
        
        if column == 1:  # Columna de Unidad
            if self.sort_ascending:
                self.update_status(f"Ordenado por Unidad: H1 → H13 ({direction})", "blue")
            else:
                self.update_status(f"Ordenado por Unidad: H13 → H1 ({direction})", "blue")
        else:
            self.update_status(f"Ordenado por {column_names[column]} ({direction})", "blue")

    def update_sort_icons(self):
        """Actualiza los iconos de todos los botones de ordenamiento."""
        for col, btn in self.sort_buttons.items():
            if col == self.sort_column:
                # Columna activa - usar iconos más descriptivos
                if self.sort_ascending:
                    icon = "🔼"  # Flecha hacia arriba para ascendente
                    btn.config(text=icon, fg="#00FF00", bg="#2c3e50")  # Verde para ascendente
                else:
                    icon = "🔽"  # Flecha hacia abajo para descendente
                    btn.config(text=icon, fg="#FF6B6B", bg="#2c3e50")  # Rojo para descendente
            else:
                # Columna inactiva - icono neutro
                btn.config(text="🔼", fg="#CCCCCC", bg="#2c3e50")  # Gris para inactiva

    def apply_sorting(self):
        """Aplica el ordenamiento a las unidades mostradas."""
        if not self.sort_column or not self.unidades_mostradas:
            return
        
        # Obtener las unidades mostradas actualmente
        units_to_sort = self.unidades_mostradas.copy()
        
        # Crear lista de datos para ordenamiento
        sort_data = []
        for alias in units_to_sort:
            # Buscar la fila correspondiente
            fila_data = None
            for fila in self.fila_widgets_data:
                if fila['alias'] == alias:
                    fila_data = fila
                    break
            
            if fila_data:
                if self.sort_column == 1:  # Unidad (ordenamiento numérico por número de unidad)
                    # Extraer el número de unidad del formato "H1 / EUI-621;EUI-621;PICKUP"
                    sort_key = self._extract_unit_number(alias)
                elif self.sort_column == 2:  # KM (numérico)
                    km_value = fila_data['entry_km'].get()
                    sort_key = int(km_value) if km_value.isdigit() else 0
                elif self.sort_column == 3:  # A.P (numérico)
                    ap_value = fila_data['entry_ap'].get()
                    sort_key = int(ap_value) if ap_value.isdigit() else 0
                else:
                    sort_key = alias.lower()
                
                sort_data.append((sort_key, alias))
        
        # Ordenar los datos
        sort_data.sort(key=lambda x: x[0], reverse=not self.sort_ascending)
        
        # Extraer las unidades ordenadas
        sorted_units = [item[1] for item in sort_data]
        
        # Actualizar la vista con las unidades ordenadas
        self.unidades_mostradas = sorted_units
        self.reorder_table_rows()

    def _extract_unit_number(self, alias):
        """Extrae el número de unidad del alias para ordenamiento numérico correcto."""
        try:
            # Formato esperado: "H1 / EUI-621;EUI-621;PICKUP"
            # Extraer la parte "H1" y convertir a número
            if ' / ' in alias:
                unit_part = alias.split(' / ')[0]  # "H1"
                if unit_part.startswith('H'):
                    unit_number = unit_part[1:]  # "1"
                    return int(unit_number)
            # Fallback: ordenamiento alfabético
            return alias.lower()
        except (ValueError, IndexError):
            # Si no se puede extraer el número, usar ordenamiento alfabético
            return alias.lower()

    def reorder_table_rows(self):
        """Reordena las filas de la tabla según el ordenamiento actual."""
        # Ocultar todas las filas primero
        for fila_data in self.fila_widgets_data:
            self.hide_row(fila_data)
        
        # Mostrar las filas en el nuevo orden
        row_counter = 1
        for alias in self.unidades_mostradas:
            # Buscar la fila correspondiente
            for fila_data in self.fila_widgets_data:
                if fila_data['alias'] == alias:
                    # Mostrar la fila en la nueva posición
                    self.show_row(fila_data, row_counter)
                    
                    # Actualizar controles y estado
                    self.update_unit_controls_state(fila_data, 
                                                  self.controller.editing_mode if self.controller else False, 
                                                  self.get_filtro_var())
                    
                    # Actualizar observaciones
                    if self.controller:
                        self.controller.actualizar_observaciones_gui(
                            fila_data['entry_km'], fila_data['entry_ap'], fila_data['entry_po'],
                            fila_data['lbl_obs_km'], fila_data['lbl_obs_ap'], fila_data['lbl_obs_po']
                        )
                    
                    self.update_row_highlighting(fila_data)
                    row_counter += 1
                    break
        
        # Ajustar scroll y botones
        self.adjust_scroll_and_buttons()

    def reset_sorting_on_filter_change(self):
        """Resetea el ordenamiento cuando cambia el filtro."""
        if self.sort_column is not None:
            self.sort_column = None
            self.sort_ascending = True
            self.update_sort_icons()
            self.update_status("Ordenamiento reseteado al cambiar filtro", "green")

    def crear_filas_unidades(self):
        """Crea las filas de unidades con mejor estilo y funcionalidad."""
        vcmd = (self.root.register(self.controller.validar_entrada_campo), '%P')
        
        for i, alias in enumerate(self.controller.model.UNIDADES_DISPONIBLES, start=1):
            self.crear_fila_unidad(i, alias, vcmd)

    def crear_fila_unidad(self, i, alias, vcmd):
        """Crea una fila individual de unidad con todos sus widgets."""
        var_chk = tk.BooleanVar()
        
        # Label de unidad sin borde
        lbl_unidad = tk.Label(self.scrollable_frame, text=alias, width=16,
                            font=self.font_tabla, anchor="w", bg="white",
                            relief=tk.FLAT, bd=0, padx=5)

        # Campos de entrada con mejor estilo - CENTRADOS Y EN NEGRITA
        entry_km = tk.Entry(self.scrollable_frame, width=12, validate="key",
                        validatecommand=vcmd, state='disabled', bg="white",
                        font=("Segoe UI", 12, "bold"), relief=tk.SOLID, bd=1,
                        justify=tk.CENTER)
        entry_ap = tk.Entry(self.scrollable_frame, width=12, validate="key",
                        validatecommand=vcmd, state='disabled', bg="white",
                        font=("Segoe UI", 12, "bold"), relief=tk.SOLID, bd=1,
                        justify=tk.CENTER)

        # Cambio de Spinbox a Entry normal para PO
        entry_po = tk.Entry(self.scrollable_frame, width=8, validate="key",
                        validatecommand=vcmd, state='disabled', bg="white",
                        font=("Segoe UI", 12, "bold"), relief=tk.SOLID, bd=1,
                        justify=tk.CENTER)

        # Frame de turnos con mejor organización
        turnos_frame = tk.Frame(self.scrollable_frame, bg="white", relief=tk.FLAT, bd=0)
        check_vars_turnos = {
            'NOCHE': tk.BooleanVar(),
            'DÍA': tk.BooleanVar(),
            'TARDE': tk.BooleanVar()
        }

        # Checkbox principal sin borde
        chk_widget = tk.Checkbutton(self.scrollable_frame, variable=var_chk,
                                command=self.controller.actualizar_contadores,
                                bg="white", activebackground="white",
                                relief=tk.FLAT, bd=0)

        # Checkboxes de turnos sin borde
        for turno in ['NOCHE', 'DÍA', 'TARDE']:
            chk_turno = tk.Checkbutton(turnos_frame, text=turno, variable=check_vars_turnos[turno],
                                    bg="white", anchor='w', state='normal', font=self.font_base,
                                    relief=tk.FLAT, bd=0)
            chk_turno.pack(side='left', padx=3, pady=2)

        # Labels de observaciones con mejor estilo
        lbl_obs_km = tk.Label(self.scrollable_frame, text="---", width=25, 
                             bg="#F8F9FA", font=("Segoe UI", 12, "bold"), relief=tk.SOLID, bd=1)
        lbl_obs_ap = tk.Label(self.scrollable_frame, text="---", width=25, 
                             bg="#F8F9FA", font=("Segoe UI", 12, "bold"), relief=tk.SOLID, bd=1)
        lbl_obs_po = tk.Label(self.scrollable_frame, text="---", width=25, 
                             bg="#F8F9FA", font=("Segoe UI", 12, "bold"), relief=tk.SOLID, bd=1)

        # Combobox de ZONA
        var_zona = tk.StringVar(value="")
        cmb_zona = ttk.Combobox(self.scrollable_frame, textvariable=var_zona,
                                values=["NORTE", "CENTRO", "SUR", "ENACE"],
                                state="readonly",
                                width=10,
                                font=("Segoe UI", 11, "bold"))

        # Almacenar los widgets y sus variables
        self.fila_widgets_data.append({
            'var_chk': var_chk,
            'alias': alias,
            'chk_widget': chk_widget,
            'lbl_unidad': lbl_unidad,
            'entry_km': entry_km,
            'entry_ap': entry_ap,
            'entry_po': entry_po,
            'turnos_frame': turnos_frame,
            'check_vars_turnos': check_vars_turnos,
            'var_zona': var_zona,
            'cmb_zona': cmb_zona,
            'lbl_obs_km': lbl_obs_km,
            'lbl_obs_ap': lbl_obs_ap,
            'lbl_obs_po': lbl_obs_po,
            'row_index': i
        })

        # Posicionamiento inicial (grid_remove para ocultar inicialmente)
        self.posicionar_widgets_fila(i, chk_widget, lbl_unidad, entry_km, entry_ap, 
                                   entry_po, turnos_frame, cmb_zona, lbl_obs_km, lbl_obs_ap, lbl_obs_po)

        # Bind events
        self.configurar_eventos_fila(entry_km, entry_ap, entry_po, lbl_obs_km, lbl_obs_ap, lbl_obs_po, var_chk)

    def posicionar_widgets_fila(self, i, chk_widget, lbl_unidad, entry_km, entry_ap, 
                              entry_po, turnos_frame, cmb_zona, lbl_obs_km, lbl_obs_ap, lbl_obs_po):
        """Posiciona los widgets de una fila en la grilla."""
        widgets_to_grid = [
            chk_widget, lbl_unidad, entry_km, entry_ap, entry_po,
            turnos_frame, cmb_zona, lbl_obs_km, lbl_obs_ap, lbl_obs_po
        ]
        for col, widget in enumerate(widgets_to_grid):
            widget.grid(row=i, column=col, sticky="ew", padx=1, pady=1)
            widget.grid_remove()  # Ocultar inicialmente

    def configurar_eventos_fila(self, entry_km, entry_ap, entry_po, lbl_obs_km, lbl_obs_ap, lbl_obs_po, var_chk):
        """Configura los eventos para una fila de unidad, incluyendo actualización automática del sombreado"""
        # Función para actualizar observaciones y resaltado
        def update_observaciones_and_highlight(*args):
            self.controller.actualizar_observaciones_gui(entry_km, entry_ap, entry_po, lbl_obs_km, lbl_obs_ap, lbl_obs_po)
            # Encontrar la fila_data correspondiente a estos widgets
            for fila_data in self.fila_widgets_data:
                if (fila_data['entry_km'] == entry_km and 
                    fila_data['entry_ap'] == entry_ap and 
                    fila_data['entry_po'] == entry_po):
                    self.update_row_highlighting(fila_data)
                    break
        
        # Bind events para actualización de observaciones y resaltado
        for entry in (entry_km, entry_ap, entry_po):
            entry.bind("<KeyRelease>", lambda e: update_observaciones_and_highlight())
            entry.bind("<FocusOut>", lambda e: update_observaciones_and_highlight())
        
        # Trace para checkbox principal
        var_chk.trace_add("write", lambda name, index, mode, v=var_chk, k=entry_km, a=entry_ap, p=entry_po, 
                        lk=lbl_obs_km, la=lbl_obs_ap, lp=lbl_obs_po: 
                        self.controller.on_unit_checkbox_toggle(v, k, a, p, lk, la, lp))

    def create_tooltip(self, widget, text):
        """Crea un tooltip para un widget."""
        def enter(event):
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            label = tk.Label(self.tooltip, text=text, background="yellow", relief="solid", borderwidth=1)
            label.pack()
        def leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def create_widgets(self):
        """Crea y posiciona todos los widgets de la interfaz con diseño moderno y ahora con pestañas."""
        if not self.controller:
            raise RuntimeError("Controller must be set before calling create_widgets on View.")
        self.main_frame = tk.Frame(self.root, bg=self.COLOR_FONDO, padx=15, pady=15)
        self.main_frame.pack(expand=True, fill=tk.BOTH)
        self.crear_header()
        self.crear_toolbar()
        self.notebook = ttk.Notebook(self.main_frame, style='ModernNotebook.TNotebook')
        self.notebook.pack(expand=True, fill=tk.BOTH)
        self.tab_reporte_km = tk.Frame(self.notebook, bg=self.COLOR_FONDO)
        # Agregar pestañas con iconos y texto
        if self.icon_tab_km:
            self.notebook.add(self.tab_reporte_km, text="Reporte KM", image=self.icon_tab_km, compound='left')
        else:
            self.notebook.add(self.tab_reporte_km, text="Reporte KM")
        self.create_unit_table(parent=self.tab_reporte_km)
        self.create_bottom_buttons(parent=self.tab_reporte_km)
        self.configure_styles()
        self.configurar_eventos_globales()
        self.configurar_atajos_avanzados()

    def crear_header(self):
        """Crea el header moderno de la aplicación."""
        # Aumentar la altura del header para que la imagen se vea completamente
        header = tk.Frame(self.main_frame, bg=self.COLOR_HEADER, height=165, pady=15)
        header.pack(fill=tk.X, pady=(0, 15))
        header.pack_propagate(False)  # Mantener altura fija
        
        # Contenedor principal centrado para imagen y textos
        content_frame = tk.Frame(header, bg=self.COLOR_HEADER)
        content_frame.pack(expand=True, fill=tk.BOTH, padx=15, pady=5)
        
        # Frame central que contendrá imagen y texto juntos
        center_frame = tk.Frame(content_frame, bg=self.COLOR_HEADER)
        center_frame.pack(expand=True, fill=tk.BOTH)
        
        # Frame horizontal para imagen y texto pegados
        logo_text_frame = tk.Frame(center_frame, bg=self.COLOR_HEADER)
        logo_text_frame.pack(expand=True)
        
        # Cargar y mostrar la imagen
        try:
            image_path = os.path.join("help", "Main.png")
            if os.path.exists(image_path):
                # Cargar imagen y redimensionar manteniendo proporción
                from PIL import Image, ImageTk
                original_image = Image.open(image_path)
                
                # Calcular dimensiones manteniendo proporción - aumentar el tamaño máximo
                max_size = 120  # Aumentado de 100 a 120
                width, height = original_image.size
                
                # Calcular nueva dimensión manteniendo proporción
                if width > height:
                    new_width = max_size
                    new_height = int((height * max_size) / width)
                else:
                    new_height = max_size
                    new_width = int((width * max_size) / height)
                
                resized_image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(resized_image)
                
                # Frame para la imagen - sin padding extra, pegada al texto
                image_frame = tk.Frame(logo_text_frame, bg=self.COLOR_HEADER, width=new_width, height=new_height)
                image_frame.pack(side=tk.LEFT, padx=(0, 10))  # Solo 10px de separación
                image_frame.pack_propagate(False)  # Mantener tamaño fijo
                
                # Centrar la imagen en el frame
                logo_label = tk.Label(image_frame, image=self.logo_image, bg=self.COLOR_HEADER)
                logo_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            else:
                # Si no existe la imagen, crear un placeholder
                image_frame = tk.Frame(logo_text_frame, bg=self.COLOR_HEADER, width=120, height=120)
                image_frame.pack(side=tk.LEFT, padx=(0, 10))
                image_frame.pack_propagate(False)
        except Exception as e:
            # En caso de error, crear un placeholder
            image_frame = tk.Frame(logo_text_frame, bg=self.COLOR_HEADER, width=120, height=120)
            image_frame.pack(side=tk.LEFT, padx=(0, 10))
            image_frame.pack_propagate(False)
        
        # Frame para los textos - ahora al lado de la imagen
        text_frame = tk.Frame(logo_text_frame, bg=self.COLOR_HEADER)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Título principal centrado
        title_label = tk.Label(text_frame, text="SISTEMA DE MONITOREO SERENAZGO", 
                              font=self.font_titulo, bg=self.COLOR_HEADER, fg="white")
        title_label.pack(anchor=tk.CENTER, pady=(0, 5))
        
        # Subtítulo centrado
        subtitle_label = tk.Label(text_frame, text="Control de KM, Auxilio Público y Parte de Ocurrencias", 
                                 font=self.font_subtitulo, bg=self.COLOR_HEADER, fg="#bdc3c7")
        subtitle_label.pack(anchor=tk.CENTER, pady=(5, 5))
        
        # Instrucción centrada
        instruction_label = tk.Label(text_frame, text="💡 Presiona ESC para cerrar la ventana", 
                                    font=self.font_status, bg=self.COLOR_HEADER, fg="#FFD700")
        instruction_label.pack(anchor=tk.CENTER, pady=(5, 0))

    def crear_toolbar(self):
        """Crea la barra de herramientas superior con mejor organización."""
        toolbar_frame = tk.Frame(self.main_frame, bg=self.COLOR_FONDO, pady=10)
        toolbar_frame.pack(fill=tk.X, pady=(0, 15))

        # SECCIÓN IZQUIERDA: Búsqueda mejorada
        self.crear_seccion_busqueda(toolbar_frame)
        
        # SECCIÓN CENTRAL: Filtros con mejor estilo
        self.crear_seccion_filtros(toolbar_frame)
        
        # SECCIÓN DERECHA: Enlaces y tiempo
        self.crear_seccion_enlaces_tiempo(toolbar_frame)
        
        # Barra de estado mejorada
        self.crear_barra_estado()

    def crear_seccion_busqueda(self, parent):
        """Crea la sección de búsqueda con diseño moderno."""
        search_frame = tk.Frame(parent, bg=self.COLOR_FONDO)
        search_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(search_frame, text="🔍 Buscar:", font=self.font_boton, 
                bg=self.COLOR_FONDO, fg=self.COLOR_HEADER).pack(side=tk.LEFT)

        # Frame para contener la entrada y el botón de limpiar
        entry_frame = tk.Frame(search_frame, bg=self.COLOR_FONDO)
        entry_frame.pack(side=tk.LEFT, padx=(10, 0))

        self.search_entry = tk.Entry(entry_frame, textvariable=self.busqueda_var, 
                                width=30, font=self.font_base, relief=tk.SOLID, bd=1,
                                bg="white", fg=self.COLOR_HEADER)
        self.search_entry.pack(side=tk.LEFT, padx=5, ipady=3)
        self.search_entry.bind('<KeyRelease>', lambda e: self.controller.debounced_search())

        # Botón de limpiar búsqueda (inicialmente oculto)
        self.clear_search_btn = ttk.Button(entry_frame, text="✘", width=3,
                                        command=self._clear_search,
                                        style='Danger.TButton')
        self.clear_search_btn.pack(side=tk.LEFT, padx=(2, 0))
        self.clear_search_btn.pack_forget()  # Ocultar inicialmente

        # Configurar el rastreo de cambios en la variable de búsqueda
        self.busqueda_var.trace_add('write', self._toggle_clear_button)

    def crear_seccion_filtros(self, parent):
        """Crea la sección de filtros con mejor diseño."""
        filter_frame = tk.Frame(parent, bg=self.COLOR_FONDO)
        filter_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(filter_frame, text="🔎 FILTROS:", font=self.font_boton, 
                bg=self.COLOR_FONDO, fg=self.COLOR_HEADER).pack(side=tk.LEFT)
        
        # Botones de filtro con estilo moderno
        filters = ["TODAS", "PICKUP", "AUTOS", "MANUAL"]
        self.filter_buttons = {}
        
        buttons_frame = tk.Frame(filter_frame, bg=self.COLOR_FONDO)
        buttons_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        for filtro in filters:
            btn = ttk.Radiobutton(buttons_frame, text=filtro, variable=self.filtro_var,
                                value=filtro, command=lambda f=filtro: self.on_filter_change(f),
                                style='Filter.TRadiobutton')
            btn.pack(side=tk.LEFT, padx=3)
            self.filter_buttons[filtro] = btn

    def on_filter_change(self, filtro):
        """Maneja el cambio de filtro y resetea el ordenamiento."""
        # Resetear ordenamiento
        self.reset_sorting_on_filter_change()
        
        # Aplicar el filtro
        if self.controller:
            self.controller.aplicar_filtro(filtro)

    def crear_seccion_enlaces_tiempo(self, parent):
        """Crea la sección de enlaces y tiempo con mejor organización."""
        right_frame = tk.Frame(parent, bg=self.COLOR_FONDO)
        right_frame.pack(side=tk.RIGHT, padx=10)
        
        # Botones de enlaces modernos
        links_frame = tk.Frame(right_frame, bg=self.COLOR_FONDO)
        links_frame.pack(side=tk.LEFT, padx=10)
        
        btn_geo = ttk.Button(links_frame, text="🌍 Wialon",
                            command=self.mostrar_opciones_wialon,
                            style='Wialon.TButton')
        btn_geo.pack(side=tk.LEFT, padx=3)
        self.create_tooltip(btn_geo, "🛰️ Opciones Wialon (URL / KM Tiempo Real)")
        
        btn_sipcop = ttk.Button(links_frame, text="🗺️ SIPCOP-M",
                            command=self.controller.open_sipcop,
                            style='Sipcop.TButton')
        btn_sipcop.pack(side=tk.LEFT, padx=3)
        self.create_tooltip(btn_sipcop, "🇵🇪 seguridadciudadana.mininter.gob.pe")

        btn_visor = ttk.Button(links_frame, text="🛰️ Visor Táctico",
                            command=self.controller.open_visor_tactico,
                            style='Visor.TButton')
        btn_visor.pack(side=tk.LEFT, padx=3)
        self.create_tooltip(btn_visor, "🌐 visor-tacticos.vercel.app")
        
        # Información de tiempo y turno mejorada
        time_frame = tk.Frame(right_frame, bg=self.COLOR_FONDO, relief=tk.SOLID, bd=1, padx=10, pady=5)
        time_frame.pack(side=tk.LEFT, padx=(15, 0))
        
        tk.Label(time_frame, text="⏰", font=self.font_boton, bg=self.COLOR_FONDO).pack(side=tk.LEFT)
        tk.Label(time_frame, textvariable=self.reloj_var, fg=self.COLOR_ACCENT,
                font=self.font_boton, bg=self.COLOR_FONDO).pack(side=tk.LEFT, padx=(5, 10))
        
        self.turno_menu = ttk.Combobox(time_frame, textvariable=self.turno_var,
                     values=["NOCHE", "DÍA", "TARDE"],
                     state="disabled",  # Siempre deshabilitado
                     width=10, 
                     font=self.font_base)
        self.turno_menu.pack(side=tk.LEFT)

        # Botón de actualización de turno
        self.btn_refresh_turno = ttk.Button(time_frame, text="🔄", width=3,
                                        command=self.controller.refresh_turno,
                                        style='Refresh.TButton')
        self.btn_refresh_turno.pack(side=tk.LEFT, padx=5)
        self.create_tooltip(self.btn_refresh_turno, "Actualizar turno según hora actual")

    def crear_barra_estado(self):
        """Crea la barra de estado con mejor diseño."""
        self.status_frame = tk.Frame(self.main_frame, bg=self.COLOR_FONDO, relief=tk.SOLID, bd=1, pady=8)
        self.status_frame.pack(fill=tk.X, pady=(10, 15))
        
        # Label de estado
        self.status_label = tk.Label(self.status_frame, textvariable=self.status_var, 
                                   fg=self.COLOR_SUCCESS, font=self.font_status, bg=self.COLOR_FONDO)
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Contadores con mejor formato
        count_frame = tk.Frame(self.status_frame, bg=self.COLOR_FONDO)
        count_frame.pack(side=tk.RIGHT, padx=10)
        
        tk.Label(count_frame, textvariable=self.contador_pickup,
                font=self.font_status, fg=self.COLOR_SUCCESS, bg=self.COLOR_FONDO).pack(side=tk.LEFT, padx=15)
        tk.Label(count_frame, textvariable=self.contador_autos,
                font=self.font_status, fg=self.COLOR_ACCENT, bg=self.COLOR_FONDO).pack(side=tk.LEFT, padx=15)
        
        # Botón de información sobre ordenamiento - REMOVIDO
        # self.sort_info_btn = self.create_sort_info_button()

    def configurar_eventos_globales(self):
        """Configura eventos globales de la aplicación."""
        # Eventos de filtros con Alt
        self.root.bind('<Alt-t>', lambda e: self.on_filter_change("TODAS"))
        self.root.bind('<Alt-p>', lambda e: self.on_filter_change("PICKUP"))
        self.root.bind('<Alt-a>', lambda e: self.on_filter_change("AUTOS"))
        self.root.bind('<Alt-m>', lambda e: self.on_filter_change("MANUAL"))

        # Eventos de ordenamiento con Ctrl - REMOVIDOS (ahora se manejan en configurar_atajos_avanzados)
        # self.root.bind('<Control-1>', lambda e: self.toggle_sort(1))  # Ctrl+1 para ordenar por Unidad
        # self.root.bind('<Control-2>', lambda e: self.toggle_sort(2))  # Ctrl+2 para ordenar por KM
        # self.root.bind('<Control-3>', lambda e: self.toggle_sort(3))  # Ctrl+3 para ordenar por A.P
        # self.root.bind('<Control-r>', lambda e: self.reset_sorting_on_filter_change())  # Ctrl+R para resetear ordenamiento

        # Eventos de navegación por filas
        self.root.bind('<Return>', lambda e: self.handle_enter_key())
        self.root.bind('<Escape>', lambda e: self.handle_escape_key())
        self.root.bind('<Control-x>', lambda e: self.handle_ctrl_x())

        # Evento de escape original (ahora manejado por handle_escape_key)
        # self.root.bind("<Escape>", lambda e: self.controller.confirmar_salida())
        self.root.protocol("WM_DELETE_WINDOW", self.controller.confirmar_salida)

    def handle_enter_key(self):
        """Maneja la tecla Enter para navegación por filas."""
        if self.navigation_mode:
            # Si estamos en modo navegación, mover a la siguiente fila
            self.navigate_to_next_row()
        else:
            # Si no estamos en modo navegación, activarlo
            self.toggle_navigation_mode()

    def handle_escape_key(self):
        """Maneja la tecla Escape."""
        if self.navigation_mode:
            # Si no estamos en modo navegación, desactivarlo
            self.toggle_navigation_mode()
        else:
            # Si no estamos en modo navegación, confirmar salida
            self.controller.confirmar_salida()

    def handle_ctrl_x(self):
        """Maneja Ctrl+X para desactivar el modo de navegación."""
        if self.navigation_mode:
            self.toggle_navigation_mode()

    def _clear_search(self):
        """Limpia el contenido de la búsqueda y enfoca el campo."""
        self.busqueda_var.set("")
        self.search_entry.focus_set()
        
        # Obtener el filtro actual
        current_filter = self.filtro_var.get()
        
        # Si el filtro es MANUAL, aplicar sin abrir ventana de selección
        if current_filter == "MANUAL":
            self.controller.aplicar_filtro(current_filter, skip_manual_dialog=True)
        else:
            # Para otros filtros, usar la búsqueda debounced normal
            self.controller.debounced_search()

    def _toggle_clear_button(self, *args):
        """Muestra u oculta el botón de limpiar según si hay texto."""
        if self.busqueda_var.get():
            self.clear_search_btn.pack(side=tk.LEFT, padx=(2, 0))
        else:
            self.clear_search_btn.pack_forget()

    def configure_styles(self):
        """Configura los estilos ttk para una apariencia moderna y consistente."""
        style = ttk.Style()
        style.theme_use('clam')  # Usar un tema moderno

        # --- ESTILO PARA NOTEBOOK (PESTAÑAS) ---
        style.configure('ModernNotebook.TNotebook',
            background=self.COLOR_FONDO,
            borderwidth=0,
            relief='flat')
        style.configure('ModernNotebook.TNotebook.Tab',
            font=self.font_boton,
            padding=[20, 8],
            background=self.COLOR_HEADER,
            foreground='white',
            borderwidth=0,
            relief='flat')
        style.map('ModernNotebook.TNotebook.Tab',
            background=[('selected', self.COLOR_ACCENT), ('active', self.COLOR_ACCENT)],
            foreground=[('selected', 'white'), ('active', 'white')])
        # --- FIN ESTILO NOTEBOOK ---

        # ESTILOS DE BOTON REFRESH
        style.configure('Refresh.TButton',
                font=("Segoe UI", 10),
                padding=(2, 2),
                foreground='white',
                background='#34495e',  # Azul oscuro
                relief='flat')
        style.map('Refresh.TButton',
                background=[('active', '#2c3e50'), ('pressed', '#1a252f')])

        # ESTILOS DE BOTONES MEJORADOS
        style.configure('TButton', 
                       font=self.font_boton, 
                       padding=(10, 8),
                       relief='flat')
        
        # Botones de acento (principales)
        style.configure('Accent.TButton', 
                       font=self.font_boton, 
                       padding=(12, 10),
                       foreground='white', 
                       background=self.COLOR_ACCENT,
                       relief='flat')
        style.map('Accent.TButton', 
                 background=[('active', '#2980b9'), ('pressed', '#21618c')])
        
        # Botones de éxito
        style.configure('Success.TButton',
                       font=self.font_boton,
                       padding=(10, 8),
                       foreground='white',
                       background=self.COLOR_SUCCESS,
                       relief='flat')
        style.map('Success.TButton',
                 background=[('active', '#229954'), ('pressed', '#1e8449')])

        # Botón Wialon (Naranja)
        style.configure('Wialon.TButton',
                       font=self.font_boton,
                       padding=(10, 8),
                       foreground='white',
                       background='#e67e22',
                       relief='flat')
        style.map('Wialon.TButton',
                 background=[('active', '#d35400'), ('pressed', '#ba4a00')])

        # Botón SIPCOP-M (Verde)
        style.configure('Sipcop.TButton',
                       font=self.font_boton,
                       padding=(10, 8),
                       foreground='white',
                       background='#27ae60',
                       relief='flat')
        style.map('Sipcop.TButton',
                 background=[('active', '#229954'), ('pressed', '#1e8449')])

        # Botón Visor Táctico (Púrpura)
        style.configure('Visor.TButton',
                       font=self.font_boton,
                       padding=(10, 8),
                       foreground='white',
                       background='#8e44ad',
                       relief='flat')
        style.map('Visor.TButton',
                 background=[('active', '#7d3c98'), ('pressed', '#6c3483')])
        
        # Botones de peligro
        style.configure('Danger.TButton',
                       font=self.font_boton,
                       padding=(8, 6),
                       foreground='white',
                       background=self.COLOR_DANGER,
                       relief='flat')
        style.map('Danger.TButton',
                 background=[('active', '#c0392b'), ('pressed', '#a93226')])
        
        # Botones informativos
        style.configure('Info.TButton',
                       font=self.font_boton,
                       padding=(6, 4),
                       foreground='white',
                       background='#17a2b8',  # Azul informativo
                       relief='flat')
        style.map('Info.TButton',
                 background=[('active', '#138496'), ('pressed', '#117a8b')])
        
        # Estilo para botones de filtro (radiobuttons)
        style.configure('Filter.TRadiobutton', 
                       font=self.font_base, 
                       padding=(8, 6),
                       relief='flat')
        style.map('Filter.TRadiobutton', 
                 background=[('selected', self.COLOR_ACCENT), ('active', '#ecf0f1')],
                 foreground=[('selected', 'white')])
        
        # Estilo para combobox
        style.configure('TCombobox', 
                       font=self.font_base, 
                       padding=(5, 5),
                       relief='solid')

        # Estilo para LabelFrames modernos
        style.configure('Modern.TLabelframe',
                       background=self.COLOR_FONDO,
                       borderwidth=1,
                       relief='solid')
        style.configure('Modern.TLabelframe.Label',
                       background=self.COLOR_FONDO,
                       foreground=self.COLOR_HEADER,
                       font=self.font_boton)

    def create_unit_table(self, parent=None):
        if parent is None:
            parent = self.main_frame
        """Crea la tabla donde se muestran las unidades con diseño moderno."""
        table_frame = tk.Frame(parent, bg=self.COLOR_FONDO, relief=tk.SOLID, bd=1)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Configurar scroll con mejor aspecto
        self.canvas = tk.Canvas(table_frame, bg="white", highlightthickness=0,
                               relief=tk.FLAT, bd=0)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="white")
        
        self.scrollable_frame.bind(
            "<Configure>", 
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Distribución mejorada del espacio
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Crear encabezados y filas
        self.crear_encabezados_tabla()
        self.crear_filas_unidades()

        # Configurar scroll con mouse wheel
        self.configurar_mouse_wheel()

    def configurar_mouse_wheel(self):
        """Configura el scroll con rueda del mouse."""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def _bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
        
        self.canvas.bind('<Enter>', _bind_to_mousewheel)
        self.canvas.bind('<Leave>', _unbind_from_mousewheel)

    def create_bottom_buttons(self, parent=None):
        if parent is None:
            parent = self.main_frame
        """Crea los botones de acción en la parte inferior con organización moderna."""
        btn_frame = tk.Frame(parent, bg=self.COLOR_FONDO, pady=10)
        btn_frame.pack(fill=tk.X)
        
        # GRUPO DE ACCIONES PRINCIPALES (IZQUIERDA)
        action_frame = tk.Frame(btn_frame, bg=self.COLOR_FONDO)
        action_frame.pack(side=tk.LEFT, padx=10)
        
        self.btn_editar = ttk.Button(action_frame, text="✏️ Editar Datos", 
                                command=self.controller.editar_datos,
                                style='Accent.TButton')
        self.btn_editar.pack(side=tk.LEFT, padx=5)
        
        self.btn_guardar = ttk.Button(action_frame, text="💾 Guardar", 
                                    command=self.controller.guardar_datos,
                                    style='Success.TButton', state=tk.DISABLED)
        self.btn_guardar.pack(side=tk.LEFT, padx=5)
        
        self.btn_limpiar = ttk.Button(action_frame, text="🧹 Limpiar", 
                                    command=self.controller.limpiar_formulario,
                                    style='TButton')
        self.btn_limpiar.pack(side=tk.LEFT, padx=5)

        # GRUPO DE ACCIONES SECUNDARIAS (DERECHA)
        secondary_frame = tk.Frame(btn_frame, bg=self.COLOR_FONDO)
        secondary_frame.pack(side=tk.RIGHT, padx=10)

        self.btn_capturar = ttk.Button(secondary_frame, text="📸 Capturar + Portapapeles", 
                                        command=self.controller.capturar_pantalla_completa,
                                        style='Success.TButton', state=tk.DISABLED)
        self.btn_capturar.pack(side=tk.LEFT, padx=5)
        
        self.btn_ultimo_registro = ttk.Button(secondary_frame, text="⏮️ Último Registro", 
                                        command=self.controller.cargar_ultimo_registro,
                                        style='TButton')
        self.btn_ultimo_registro.pack(side=tk.LEFT, padx=5)
        
        self.btn_vaciarBD = ttk.Button(secondary_frame, text="🗑️ Vaciar BD", 
                                command=self.controller.vaciar_bd_excel,
                                style='Danger.TButton')
        self.btn_vaciarBD.pack(side=tk.LEFT, padx=5)
        
        # CONFIGURAR ATAJOS ALT MEJORADOS
        self.root.bind('<Alt-e>', lambda e: self.controller.editar_datos())
        self.root.bind('<Alt-g>', lambda e: self.btn_guardar.invoke() if self.btn_guardar['state'] == tk.NORMAL else None)
        self.root.bind('<Alt-l>', lambda e: self.controller.limpiar_formulario())
        # Alt+C ahora se usa para Lista de Cámaras (removido el binding para capturar)
        self.root.bind('<Alt-u>', lambda e: self.controller.cargar_ultimo_registro())
        self.root.bind('<Alt-b>', lambda e: self.search_entry.focus())
        self.root.bind('<Alt-d>', lambda e: self.btn_vaciarBD.invoke())  # 🗑️ Vaciar BD

    # =================================================================
    # MÉTODOS DE ACTUALIZACIÓN Y CONTROL DE LA UI (SIN CAMBIOS MAYORES)
    # =================================================================

    def update_reloj(self, time_str):
        self.reloj_var.set(time_str)

    def update_status(self, status_str, color="green"):
        """Actualiza el mensaje de estado con color específico."""
        self.status_var.set(status_str)
        
        # Mapear colores a códigos hexadecimales
        color_map = {
            "green": self.COLOR_SUCCESS,
            "blue": self.COLOR_ACCENT,
            "red": self.COLOR_DANGER,
            "orange": self.COLOR_WARNING
        }
        
        status_color = color_map.get(color, self.COLOR_SUCCESS)
        self.status_label.config(fg=status_color)

    def update_counters(self, pickup_count, total_pickup, autos_count, total_autos):
        self.contador_pickup.set(f"🚓 Pick-ups seleccionadas: {pickup_count}/{total_pickup}")
        self.contador_autos.set(f"🚔 Autos Sedán seleccionados: {autos_count}/{total_autos}")
        # Guardar los valores actuales para usarlos después
        self.current_pickup_count = pickup_count
        self.current_autos_count = autos_count

    def show_message(self, title, message, type="info"):
        if type == "info":
            messagebox.showinfo(title, message)
        elif type == "warning":
            messagebox.showwarning(title, message)
        elif type == "error":
            messagebox.showerror(title, message)
        elif type == "askyesno":
            return messagebox.askyesno(title, message)

    def show_message_with_link(self, title, message, file_path=None, type="info"):
        """
        Muestra un mensaje con un enlace clickeable para abrir una carpeta o archivo.
        
        Args:
            title: Título del mensaje
            message: Mensaje principal
            file_path: Ruta del archivo o carpeta que se abrirá al hacer clic
            type: Tipo de mensaje (info, warning, error)
        """
        # Crear ventana personalizada
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x250")
        dialog.configure(bg='#f0f0f0')
        dialog.attributes('-topmost', True)
        
        # Centrar la ventana
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Frame principal
        main_frame = tk.Frame(dialog, bg='#f0f0f0', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Icono según el tipo
        icon_map = {
            "info": "✅",
            "warning": "⚠️", 
            "error": "❌"
        }
        icon = icon_map.get(type, "ℹ️")
        
        # Título con icono
        title_frame = tk.Frame(main_frame, bg='#f0f0f0')
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(title_frame, text=f"{icon} {title}", 
                font=('Segoe UI', 12, 'bold'), 
                bg='#f0f0f0', fg='#2c3e50').pack()
        
        # Mensaje principal - Formato específico solicitado
        if file_path and "captura" in message.lower():
            # Formato específico para capturas de pantalla
            formatted_message = f"✅ Captura exitosa\n📸Captura guardada: {file_path}\n📋 ¡También se copió al portapapeles!"
        else:
            # Formato original para otros tipos de mensajes
            formatted_message = message
        
        message_label = tk.Label(main_frame, text=formatted_message, 
                               font=('Segoe UI', 10), 
                               bg='#f0f0f0', fg='#2c3e50',
                               wraplength=450, justify=tk.LEFT)
        message_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Enlace clickeable si se proporciona una ruta
        if file_path:
            link_frame = tk.Frame(main_frame, bg='#f0f0f0')
            link_frame.pack(fill=tk.X, pady=(0, 20))
            
            # Función para abrir la carpeta
            def open_folder():
                try:
                    import subprocess
                    import platform
                    
                    if platform.system() == "Windows":
                        # En Windows, abrir la carpeta contenedora
                        folder_path = os.path.dirname(os.path.abspath(file_path))
                        
                        # Verificar que la carpeta existe antes de intentar abrirla
                        if not os.path.exists(folder_path):
                            messagebox.showerror("Error", f"La carpeta no existe: {folder_path}")
                            return
                        
                        # Intentar abrir con explorer, pero manejar errores específicos
                        try:
                            subprocess.run(['explorer', folder_path], check=True, timeout=10)
                        except subprocess.TimeoutExpired:
                            messagebox.showerror("Error", "Tiempo de espera agotado al abrir la carpeta")
                        except subprocess.CalledProcessError as e:
                            # Si explorer falla, intentar con start
                            try:
                                subprocess.run(['start', folder_path], shell=True, check=True, timeout=10)
                            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                                messagebox.showerror("Error", f"No se pudo abrir la carpeta: {folder_path}")
                        except FileNotFoundError:
                            messagebox.showerror("Error", "El comando 'explorer' no está disponible en este sistema")
                    else:
                        # En otros sistemas
                        subprocess.run(['open', os.path.dirname(file_path)], check=True)
                        
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo abrir la carpeta: {str(e)}")
            
            # Crear el enlace como un botón con estilo de enlace
            link_button = tk.Button(link_frame, 
                                  text=f"📁 Abrir carpeta", 
                                  font=('Segoe UI', 10, 'underline'),
                                  fg='#3498db', 
                                  bg='#f0f0f0',
                                  bd=0, 
                                  cursor='hand2',
                                  command=open_folder)
            link_button.pack(anchor=tk.W)
            
            # Tooltip explicativo
            def show_tooltip(event):
                tooltip = tk.Toplevel(dialog)
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                
                label = tk.Label(tooltip, text="Haz clic para abrir la carpeta", 
                               bg='#2c3e50', fg='white', 
                               font=('Segoe UI', 9), padx=5, pady=3)
                label.pack()
                
                def hide_tooltip(event):
                    tooltip.destroy()
                
                link_button.bind('<Leave>', hide_tooltip)
                tooltip.bind('<Leave>', hide_tooltip)
            
            link_button.bind('<Enter>', show_tooltip)
        
        # Botón de cerrar
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        close_button = tk.Button(button_frame, 
                               text="Cerrar", 
                               font=('Segoe UI', 10),
                               bg='#3498db', 
                               fg='white',
                               bd=0, 
                               padx=20, 
                               pady=5,
                               command=dialog.destroy)
        close_button.pack(side=tk.RIGHT)
        
        # Centrar la ventana en la pantalla
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Esperar a que se cierre la ventana
        self.root.wait_window(dialog)

    def get_filtro_var(self):
        return self.filtro_var.get()

    def get_turno_var(self):
        return self.turno_var.get()

    def get_busqueda_var(self):
        return self.busqueda_var.get()

    def get_fila_widgets_data(self):
        return self.fila_widgets_data

    def get_unit_selection_data(self):
        """
        Retorna los datos de las unidades seleccionadas en la tabla para el controlador.
        """
        selected_units_data = []
        for fila_data in self.fila_widgets_data:
            if fila_data['var_chk'].get() and fila_data['alias'] in self.unidades_mostradas:
                km = fila_data['entry_km'].get()
                ap = fila_data['entry_ap'].get()
                po = fila_data['entry_po'].get()
                turnos = [t for t, var in fila_data['check_vars_turnos'].items() if var.get()]
                zona = fila_data['var_zona'].get().strip().upper()
                jurisdiccion = zona if zona in ["NORTE", "CENTRO", "SUR", "ENACE"] else (zona or "")
                selected_units_data.append({
                    'alias': fila_data['alias'],
                    'km': km,
                    'ap': ap,
                    'po': po,
                    'turnos_seleccionados': turnos,
                    'jurisdiccion': jurisdiccion,
                    'zona': zona or jurisdiccion
                })
        return selected_units_data

    def set_editing_mode(self, enabled):
        """Habilita o deshabilita los controles de edición."""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.btn_guardar.config(state=state)
        self.btn_capturar.config(state=state)

        for fila_data in self.fila_widgets_data:
            entry_km = fila_data['entry_km']
            entry_ap = fila_data['entry_ap']
            entry_po = fila_data['entry_po']
            
            # Solo habilitar/deshabilitar si la unidad está visible y marcada
            if fila_data['alias'] in self.unidades_mostradas:
                self.update_row_highlighting(fila_data)
                if fila_data['var_chk'].get() and enabled: # Si está marcada y habilitando edición
                    entry_km.config(state=tk.NORMAL)
                    entry_ap.config(state=tk.NORMAL)
                    entry_po.config(state=tk.NORMAL)
                else: # Deshabilitar si no está marcada o deshabilitando edición
                    entry_km.config(state=tk.DISABLED)
                    entry_ap.config(state=tk.DISABLED)
                    entry_po.config(state=tk.DISABLED)
            else: # Si la unidad no está mostrada, siempre deshabilitar
                entry_km.config(state=tk.DISABLED)
                entry_ap.config(state=tk.DISABLED)
                entry_po.config(state=tk.DISABLED)

    def show_unit_selection_window(self, available_units, current_selected_units):
        """Muestra una ventana para la selección manual de unidades con diseño moderno."""
        ventana_seleccion = tk.Toplevel(self.root)
        ventana_seleccion.title("🔧 Selección Manual de Unidades")
        ventana_seleccion.geometry("500x600")
        ventana_seleccion.configure(bg=self.COLOR_FONDO)
        ventana_seleccion.attributes('-topmost', True)

        vars_seleccion = {alias: tk.BooleanVar(value=(alias in current_selected_units))
                         for alias in available_units}

        # Header moderno
        header_frame = tk.Frame(ventana_seleccion, bg=self.COLOR_HEADER, pady=15)
        header_frame.pack(fill=tk.X)
        
        tk.Label(header_frame, text="🔧 Seleccione las unidades a mostrar:",
                font=self.font_subtitulo, bg=self.COLOR_HEADER, fg="white").pack()

        # Frame principal con scroll
        main_frame = tk.Frame(ventana_seleccion, bg=self.COLOR_FONDO)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Canvas con scrollbar para la lista
        canvas = tk.Canvas(main_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Checkboxes con mejor estilo
        for alias in available_units:
            frame_item = tk.Frame(scrollable_frame, bg="white", pady=5)
            frame_item.pack(fill=tk.X, padx=10)
            
            chk = tk.Checkbutton(frame_item, text=alias, variable=vars_seleccion[alias],
                               font=self.font_base, bg="white", anchor="w")
            chk.pack(side=tk.LEFT)

        selected_from_dialog = []
        def confirmar_seleccion():
            nonlocal selected_from_dialog
            selected_from_dialog.clear()
            for alias, var in vars_seleccion.items():
                if var.get():
                    selected_from_dialog.append(alias)
            ventana_seleccion.destroy()

        # Botones con estilo moderno
        btn_frame = tk.Frame(ventana_seleccion, bg=self.COLOR_FONDO, pady=15)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="✅ Confirmar Selección", 
                  command=confirmar_seleccion, style='Success.TButton').pack()

        ventana_seleccion.grab_set()
        self.register_child_window(ventana_seleccion)
        self.root.wait_window(ventana_seleccion)
        return selected_from_dialog if selected_from_dialog else current_selected_units

    def update_unit_display(self, units_to_display, filter_type, is_editing_mode, selected_units_by_checkbox=None):
        """Actualiza la visualización de las unidades en la tabla."""
        # Guardar el estado actual de navegación
        was_in_navigation_mode = self.navigation_mode
        current_highlighted_row = self.current_highlighted_row
        
        # Limpiar la lista de unidades mostradas
        self.unidades_mostradas = []
        
        # Procesar las unidades a mostrar
        for unit in units_to_display:
            # Limpiar el formato de las unidades (eliminar saltos de línea y espacios)
            cleaned_unit = unit.strip()
            if cleaned_unit:  # Solo agregar si no está vacío
                self.unidades_mostradas.append(cleaned_unit)
        
        # Primero ocultar todas las filas y desmarcar checkboxes
        for fila_data in self.fila_widgets_data:
            self.hide_row(fila_data)
            # Desmarcar checkbox para unidades que no están en la lista actual
            fila_data['var_chk'].set(False)

        row_counter = 1
        for fila_data in self.fila_widgets_data:
            alias = fila_data['alias']
            if alias in self.unidades_mostradas:
                # Configurar el estado del checkbox principal
                if filter_type in ["TODAS", "PICKUP", "AUTOS"]:
                    fila_data['var_chk'].set(True)
                elif filter_type == "MANUAL":
                    fila_data['var_chk'].set(alias in (selected_units_by_checkbox or []))

                # Mostrar la fila
                self.show_row(fila_data, row_counter)
                
                # Actualizar controles y estado
                self.update_unit_controls_state(fila_data, is_editing_mode, filter_type)
                self.controller.actualizar_observaciones_gui(
                    fila_data['entry_km'], fila_data['entry_ap'], fila_data['entry_po'],
                    fila_data['lbl_obs_km'], fila_data['lbl_obs_ap'], fila_data['lbl_obs_po']
                )
                self.update_row_highlighting(fila_data)
                
                row_counter += 1

        # Aplicar ordenamiento si está activo
        if self.sort_column is not None:
            self.apply_sorting()

        # Restaurar el resaltado de navegación si estaba activo
        if was_in_navigation_mode:
            # Ajustar el índice si es necesario
            visible_rows = [fila for fila in self.fila_widgets_data if fila['lbl_unidad'].winfo_viewable()]
            if visible_rows and current_highlighted_row >= 0:
                # Asegurar que el índice esté dentro del rango
                if current_highlighted_row >= len(visible_rows):
                    self.current_highlighted_row = 0
                else:
                    self.current_highlighted_row = current_highlighted_row
                # Aplicar el resaltado
                self.highlight_current_row()

        # Forzar actualización de la interfaz
        self.root.update_idletasks()
        self.adjust_scroll_and_buttons()

        # Forzar actualización de la tabla de personal si existe
        if hasattr(self, 'tree_personal'):
            self._actualizar_tabla_personal()

    def hide_row(self, fila_data):
        """Oculta todos los widgets de una fila."""
        widgets = [
            fila_data['chk_widget'], fila_data['lbl_unidad'], fila_data['entry_km'],
            fila_data['entry_ap'], fila_data['entry_po'], fila_data['turnos_frame'],
            fila_data['cmb_zona'],
            fila_data['lbl_obs_km'], fila_data['lbl_obs_ap'], fila_data['lbl_obs_po']
        ]
        for widget in widgets:
            widget.grid_remove()
        
        # Resetear observaciones
        fila_data['lbl_obs_km'].config(text="---", fg="black", bg="#F8F9FA")
        fila_data['lbl_obs_ap'].config(text="---", fg="black", bg="#F8F9FA")
        fila_data['lbl_obs_po'].config(text="---", fg="black", bg="#F8F9FA")

    def show_row(self, fila_data, row):
        """Muestra todos los widgets de una fila."""
        fila_data['chk_widget'].grid(row=row, column=0, sticky="ew", padx=1, pady=1)
        fila_data['lbl_unidad'].grid(row=row, column=1, sticky="ew", padx=1, pady=1)
        fila_data['entry_km'].grid(row=row, column=2, sticky="ew", padx=1, pady=1)
        fila_data['entry_ap'].grid(row=row, column=3, sticky="ew", padx=1, pady=1)
        fila_data['entry_po'].grid(row=row, column=4, sticky="ew", padx=1, pady=1)
        fila_data['turnos_frame'].grid(row=row, column=5, sticky="ew", padx=1, pady=1)
        fila_data['cmb_zona'].grid(row=row, column=6, sticky="ew", padx=1, pady=1)
        fila_data['lbl_obs_km'].grid(row=row, column=7, sticky="ew", padx=1, pady=1)
        fila_data['lbl_obs_ap'].grid(row=row, column=8, sticky="ew", padx=1, pady=1)
        fila_data['lbl_obs_po'].grid(row=row, column=9, sticky="ew", padx=1, pady=1)

    def adjust_scroll_and_buttons(self):
        """Ajusta el scroll y el estado de los botones de filtro."""
        self.scrollable_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.toggle_filter_buttons_state(self.get_busqueda_var() != "")

    def update_unit_controls_state(self, fila_data, is_editing_mode, filter_type):
        """Actualiza el estado de los controles de la unidad, manteniendo los checkboxes de turno siempre habilitados"""
        entry_km = fila_data['entry_km']
        entry_ap = fila_data['entry_ap']
        entry_po = fila_data['entry_po']
        check_vars_turnos = fila_data['check_vars_turnos']
        
        if is_editing_mode and fila_data['var_chk'].get():
            # Habilitar campos de entrada si estamos en modo edición y la unidad está marcada
            entry_km.config(state=tk.NORMAL)
            entry_ap.config(state=tk.NORMAL)
            entry_po.config(state=tk.NORMAL)
        else:
            # Deshabilitar campos de entrada si no estamos en modo edición o la unidad no está marcada
            entry_km.config(state=tk.DISABLED)
            entry_ap.config(state=tk.DISABLED)
            entry_po.config(state=tk.DISABLED)
        
        # Los checkboxes de turno siempre permanecen habilitados
        for turno, var in check_vars_turnos.items():
            chk_widget = fila_data['turnos_frame'].winfo_children()[list(check_vars_turnos.keys()).index(turno)]
            chk_widget.config(state=tk.NORMAL)
                           

    def update_row_highlighting(self, fila_data):
        """Actualiza el resaltado de una fila basado en las validaciones de los campos"""
        km = fila_data['entry_km'].get()
        ap = fila_data['entry_ap'].get()
        po = fila_data['entry_po'].get()
        
        # Obtener observaciones del modelo
        obs_km, obs_ap, obs_po = self.controller.model.calcular_observaciones(km, ap, po)
        
        # Determinar si toda la fila debe resaltarse (todos los campos válidos y completos)
        all_valid = (obs_km[0].startswith("✅") and 
                    obs_ap[0].startswith("✅") and 
                    obs_po[0].startswith("✅"))
        
        # Colores modernos para el resaltado
        highlight_color = "#d5f4e6" if all_valid else "white"  # Verde suave para válidos
        
        # Aplicar el resaltado a todos los widgets de la fila (incluyendo checkboxes de turno)
        widgets_to_highlight = [
            fila_data['chk_widget'],
            fila_data['lbl_unidad'],
            fila_data['entry_km'],
            fila_data['entry_ap'],
            fila_data['entry_po'],
            fila_data['turnos_frame'],
            fila_data['cmb_zona'],
            fila_data['lbl_obs_km'],
            fila_data['lbl_obs_ap'],
            fila_data['lbl_obs_po']
        ]
        
        for widget in widgets_to_highlight:
            try:
                if isinstance(widget, tk.Checkbutton):
                    widget.config(bg=highlight_color, activebackground=highlight_color)
                elif isinstance(widget, tk.Entry) or isinstance(widget, tk.Spinbox):
                    widget.config(bg=highlight_color, disabledbackground=highlight_color)
                elif isinstance(widget, tk.Frame):
                    widget.config(bg=highlight_color)
                    # Actualizar el fondo de los checkboxes dentro del frame
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Checkbutton):
                            child.config(bg=highlight_color, activebackground=highlight_color)
                else:
                    widget.config(bg=highlight_color)
            except tk.TclError:
                pass  # Ignorar errores con widgets que no soportan cambio de color

    def clear_form(self, clear_all=False):
        """Limpia los campos de las unidades.
        
        Args:
            clear_all: Si True, limpia todas las unidades sin importar su estado de selección.
                    Si False, solo limpia las unidades seleccionadas.
        """
        for fila_data in self.fila_widgets_data:
            if clear_all or fila_data['var_chk'].get():  # Limpiar todas o solo las seleccionadas
                # Limpiar campos
                fila_data['entry_km'].delete(0, tk.END)
                fila_data['entry_ap'].delete(0, tk.END)
                fila_data['entry_po'].delete(0, tk.END)
                
                # Desmarcar checkboxes de turnos
                for var in fila_data['check_vars_turnos'].values():
                    var.set(False)
                    
                # Resetear observaciones
                fila_data['lbl_obs_km'].config(text="---", fg="black", bg="#F8F9FA")
                fila_data['lbl_obs_ap'].config(text="---", fg="black", bg="#F8F9FA")
                
                # Resetear zona
                fila_data['var_zona'].set("")
                fila_data['lbl_obs_po'].config(text="---", fg="black", bg="#F8F9FA")
                
                # Desmarcar checkbox principal si estamos limpiando todo
                if clear_all:
                    fila_data['var_chk'].set(False)
                    
                # Actualizar resaltado de la fila
                self.update_row_highlighting(fila_data)
        
        # Limpiar el turno principal solo si estamos limpiando todo
        if clear_all:
            self.turno_var.set("")

    def get_root_coords(self):
        """Retorna las coordenadas y dimensiones de la ventana principal."""
        self.root.update_idletasks() # Asegura que las coordenadas sean actuales
        x = self.root.winfo_rootx()
        y = self.root.winfo_rooty()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        return x, y, width, height

    def toggle_filter_buttons_state(self, disable):
        """Habilita o deshabilita los botones de filtro."""
        state = tk.DISABLED if disable else tk.NORMAL
        for btn in self.filter_buttons.values():
            btn.config(state=state)

    def mostrar_contacto(self):
        """Muestra la imagen Presentacion.jpeg en una ventana pequeña, centrada, sin bordes ni barras, con la imagen ocupando todo el espacio y el enlace de WhatsApp debajo."""
        import threading
        import webbrowser
        try:
            from PIL import Image, ImageTk
        except ImportError:
            messagebox.showerror("Error", "Pillow no está instalado. No se puede mostrar la imagen de contacto.")
            return
        
        # Crear ventana sin bordes ni título
        contacto_win = tk.Toplevel(self.root)
        contacto_win.overrideredirect(True)
        contacto_win.attributes('-topmost', True)
        contacto_win.attributes('-alpha', 0.0)  # Para fade-in
        contacto_win.configure(bg="black")
        
        # Tamaño fijo de ventana
        win_w, win_h = 700, 500
        x = (contacto_win.winfo_screenwidth() // 2) - (win_w // 2)
        y = (contacto_win.winfo_screenheight() // 2) - (win_h // 2)
        contacto_win.geometry(f"{win_w}x{win_h}+{x}+{y}")
        contacto_win.update_idletasks()
        
        # Frame para la imagen (rellena toda la ventana)
        frame = tk.Frame(contacto_win, bg="black")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Cargar y escalar la imagen manteniendo proporción
        img_path = self._get_resource_path("help/Presentacion.jpeg")
        if not os.path.exists(img_path):
            tk.Label(frame, text="No se encontró la imagen Presentacion.jpeg", bg="black", fg="white").pack(expand=True)
        else:
            img = Image.open(img_path)
            # Función para redibujar la imagen al cambiar tamaño
            def update_image(event=None):
                w = win_w
                h = win_h - 50  # Dejar espacio para el enlace
                img_ratio = img.width / img.height
                win_ratio = w / h
                if win_ratio > img_ratio:
                    new_h = h
                    new_w = int(h * img_ratio)
                else:
                    new_w = w
                    new_h = int(w / img_ratio)
                img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img_resized)
                img_label.config(image=photo)
                # Mantener referencia a la imagen para evitar garbage collection
                img_label._photo = photo
                img_label.place(x=(w-new_w)//2, y=(h-new_h)//2, width=new_w, height=new_h)
            img_label = tk.Label(frame, bg="black", bd=0, highlightthickness=0)
            img_label.place(x=0, y=0, width=win_w, height=win_h-50)
            # Label tipo enlace debajo de la imagen
            link_label = tk.Label(frame, text="Contáctame por WhatsApp", fg="#25D366", bg="black", cursor="hand2", font=("Segoe UI", 16, "underline"))
            link_label.place(relx=0.5, y=win_h-35, anchor="center")
            link_url = "https://wa.me/51977201449?text=Hola%20Estimado(a),%20quisiera%20información%20sobre%20el%20sistema%20que%20ha%20desarrollado."
            link_label.bind("<Button-1>", lambda e: webbrowser.open(link_url))
            link_label.bind("<Enter>", lambda e: link_label.config(fg="#128C7E"))
            link_label.bind("<Leave>", lambda e: link_label.config(fg="#25D366"))
            # Redibujar imagen al cambiar tamaño de ventana (opcional, pero aquí tamaño es fijo)
            update_image()
        # Fade-in
        def fade_in():
            alpha = 0.0
            while alpha < 1.0:
                alpha += 0.05
                if alpha > 1.0:
                    alpha = 1.0
                contacto_win.attributes('-alpha', alpha)
                contacto_win.update()
                time.sleep(0.01)
        threading.Thread(target=fade_in, daemon=True).start()
        # Cerrar con Escape o clic derecho
        def close(event=None):
            contacto_win.destroy()
        contacto_win.bind('<Escape>', close)
        contacto_win.bind('<Button-3>', close)
        self.register_child_window(contacto_win)
        self.root.wait_window(contacto_win)

    def _get_resource_path(self, relative_path):
        """Obtiene la ruta absoluta al recurso, compatible con PyInstaller y desarrollo."""
        if hasattr(sys, '_MEIPASS'):
            # type: ignore
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def get_sort_status_text(self):
        """Retorna el texto descriptivo del estado actual de ordenamiento."""
        if not self.sort_column:
            return "Sin ordenamiento"
        
        column_names = {1: "Unidad", 2: "KM", 3: "A.P"}
        direction = "ascendente" if self.sort_ascending else "descendente"
        
        if self.sort_column == 1:  # Columna de Unidad
            if self.sort_ascending:
                return "Ordenado por Unidad: H1 → H13"
            else:
                return "Ordenado por Unidad: H13 → H1"
        else:
            return f"Ordenado por {column_names[self.sort_column]} ({direction})"

    def show_sort_info(self):
        """Muestra información sobre el ordenamiento actual."""
        if self.sort_column:
            sort_info = self.get_sort_status_text()
            self.show_message("Ordenamiento Activo", 
                            f"Ordenamiento actual: {sort_info}\n\n"
                            "Haz clic nuevamente en el encabezado para cambiar la dirección.\n"
                            "Haz clic en otro encabezado para ordenar por esa columna.", 
                            "info")

    def _crear_supervisores_operadores(self, parent):
        """Crea la sección de Supervisores y Operadores con diseño mejorado y organizado."""
        # --- SECCIÓN Supervisores y Operadores de Cámara ---
        self.operadores = []  # Lista de dicts: {"nombre": str, "op_code": str}
        self.operadores_widgets = []  # Referencias a widgets de cada fila
        self.next_op_code = 1  # Código inicial sugerido (01)

        # Frame principal con mejor espaciado
        main_container = tk.Frame(parent, bg=self.COLOR_FONDO)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Título principal de la sección
        title_frame = tk.Frame(main_container, bg=self.COLOR_FONDO)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(title_frame, text="👥 DISTRIBUCIÓN DE PERSONAL", 
                              font=("Segoe UI", 16, "bold"), 
                              bg=self.COLOR_FONDO, fg=self.COLOR_HEADER)
        title_label.pack()

        # Frame para organizar en dos columnas principales
        content_frame = tk.Frame(main_container, bg=self.COLOR_FONDO)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # --- COLUMNA IZQUIERDA: Supervisores y Operadores ---
        left_column = tk.Frame(content_frame, bg=self.COLOR_FONDO)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Sección de Supervisores
        supervisores_frame = ttk.LabelFrame(left_column, text="👤 Supervisores", 
                                           style='Modern.TLabelframe', padding=15)
        supervisores_frame.pack(fill=tk.X, pady=(0, 15))

        # Grid para supervisores con mejor alineación
        sup_t_label = tk.Label(supervisores_frame, text="👤 Supervisor (T):", 
                              font=self.font_boton, bg=self.COLOR_FONDO, anchor='w')
        sup_t_label.grid(row=0, column=0, sticky="w", pady=(0, 10), padx=(0, 10))
        
        self.sup_t_entry = tk.Entry(supervisores_frame, font=self.font_base, 
                                   relief=tk.SOLID, bd=1, bg="white")
        self.sup_t_entry.grid(row=0, column=1, sticky="ew", pady=(0, 10), padx=(0, 20))
        self.sup_t_entry.insert(0, "SUPERVISOR DE TURNO")

        sup_c_label = tk.Label(supervisores_frame, text="👤 Supervisor (C):", 
                              font=self.font_boton, bg=self.COLOR_FONDO, anchor='w')
        sup_c_label.grid(row=1, column=0, sticky="w", pady=(0, 10), padx=(0, 10))
        
        self.sup_c_entry = tk.Entry(supervisores_frame, font=self.font_base, 
                                   relief=tk.SOLID, bd=1, bg="white")
        self.sup_c_entry.grid(row=1, column=1, sticky="ew", pady=(0, 10), padx=(0, 20))
        self.sup_c_entry.insert(0, "SUPERVISOR DE CAMARA")

        # Configurar expansión de columnas
        supervisores_frame.grid_columnconfigure(1, weight=1)

        # Sección de Operadores de Cámaras
        operadores_frame = ttk.LabelFrame(left_column, text="📹 Operadores de Cámaras", 
                                         style='Modern.TLabelframe', padding=15)
        operadores_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Frame para la lista de operadores con scroll
        operadores_list_container = tk.Frame(operadores_frame, bg=self.COLOR_FONDO)
        operadores_list_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Canvas y scrollbar para operadores
        operadores_canvas = tk.Canvas(operadores_list_container, bg=self.COLOR_FONDO, 
                                     highlightthickness=0, height=150)
        operadores_scrollbar = ttk.Scrollbar(operadores_list_container, orient="vertical", 
                                           command=operadores_canvas.yview)
        self.operadores_list_frame = tk.Frame(operadores_canvas, bg=self.COLOR_FONDO)

        self.operadores_list_frame.bind(
            "<Configure>",
            lambda e: operadores_canvas.configure(scrollregion=operadores_canvas.bbox("all"))
        )

        operadores_canvas.create_window((0, 0), window=self.operadores_list_frame, anchor="nw")
        operadores_canvas.configure(yscrollcommand=operadores_scrollbar.set)

        operadores_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        operadores_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Botón para agregar operador
        btn_agregar_operador = ttk.Button(operadores_frame, text="➕ Agregar Operador", 
                                         command=self._agregar_operador,
                                         style='Success.TButton')
        btn_agregar_operador.pack(pady=(10, 0))

        # --- COLUMNA DERECHA: Descripción de Relevo ---
        right_column = tk.Frame(content_frame, bg=self.COLOR_FONDO)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # Sección de Descripción de Relevo
        relevo_frame = ttk.LabelFrame(right_column, text="📝 Descripción de Relevo de Turno", 
                                     style='Modern.TLabelframe', padding=15)
        relevo_frame.pack(fill=tk.BOTH, expand=True)

        # Text widget con scrollbar
        text_container = tk.Frame(relevo_frame, bg=self.COLOR_FONDO)
        text_container.pack(fill=tk.BOTH, expand=True)

        self.shift_text = tk.Text(text_container, font=self.font_base, 
                                 relief=tk.SOLID, bd=1, bg="white", wrap=tk.WORD)
        shift_scrollbar = ttk.Scrollbar(text_container, orient="vertical", 
                                       command=self.shift_text.yview)
        self.shift_text.configure(yscrollcommand=shift_scrollbar.set)

        self.shift_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        shift_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Inicializar con un operador por defecto
        if not self.operadores:
            self._agregar_operador()

        # --- SECCIÓN DE TABLAS ---
        # Frame para contener todas las tablas
        tables_frame = tk.Frame(main_container, bg=self.COLOR_FONDO)
        tables_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))

        # Crear todas las tablas
        self._crear_tabla_personal(tables_frame)
        self._crear_tabla_motorizados(tables_frame)
        self._crear_tabla_sierra_bravos(tables_frame)
        self._crear_tabla_bases_operativas(tables_frame)
        self._crear_tabla_prevencion(tables_frame)

        # --- BOTONES DE ACCIÓN ---
        # Frame para los botones centrados
        buttons_frame = tk.Frame(main_container, bg=self.COLOR_FONDO)
        buttons_frame.pack(fill=tk.X, pady=(30, 0))

        # Frame interno para centrar los botones
        buttons_center_frame = tk.Frame(buttons_frame, bg=self.COLOR_FONDO)
        buttons_center_frame.pack(expand=True)

        # Botón Guardar
        self.btn_guardar_distribucion = ttk.Button(buttons_center_frame, 
                                                  text="🟩 Guardar", 
                                                  command=self._guardar_distribucion,
                                                  style='Success.TButton')
        self.btn_guardar_distribucion.pack(side=tk.LEFT, padx=10, ipadx=20, ipady=8)

        # Botón Limpiar
        self.btn_limpiar_distribucion = ttk.Button(buttons_center_frame, 
                                                  text="🧹 Limpiar", 
                                                  command=self._limpiar_distribucion,
                                                  style='TButton')
        self.btn_limpiar_distribucion.pack(side=tk.LEFT, padx=10, ipadx=20, ipady=8)

        # Botón Imprimir
        self.btn_imprimir_distribucion = ttk.Button(buttons_center_frame, 
                                                   text="🖨️ Imprimir", 
                                                   command=self._imprimir_distribucion,
                                                   style='Accent.TButton')
        self.btn_imprimir_distribucion.pack(side=tk.LEFT, padx=10, ipadx=20, ipady=8)

    def _guardar_distribucion(self):
        """Guarda los datos de distribución de personal."""
        try:
            # Recopilar todos los datos
            datos_distribucion = {
                'supervisores': {
                    'supervisor_t': self.sup_t_entry.get(),
                    'supervisor_c': self.sup_c_entry.get()
                },
                'operadores': self.operadores,
                'relevo_turno': self.shift_text.get("1.0", tk.END).strip(),
                'personal': self.personal_data,
                'motorizados': self.motorizados_data,
                'sierra_bravos': self.sierra_bravos_data,
                'bases_operativas': self.bases_operativas_data,
                'prevencion': self.prevencion_data,
                'fecha_guardado': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Guardar en archivo JSON
            import json
            filename = f"distribucion_personal_{time.strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(datos_distribucion, f, ensure_ascii=False, indent=2)
            
            self.show_message("✅ Guardado Exitoso", 
                            f"Los datos de distribución se han guardado en:\n{filename}", 
                            "info")
            
        except Exception as e:
            self.show_message("❌ Error al Guardar", 
                            f"No se pudieron guardar los datos:\n{str(e)}", 
                            "error")

    def _limpiar_distribucion(self):
        """Limpia todos los campos de distribución de personal."""
        if self.show_message("🧹 Limpiar Datos", 
                           "¿Estás seguro de que quieres limpiar todos los datos de distribución?", 
                           "askyesno"):
            
            # Limpiar supervisores
            self.sup_t_entry.delete(0, tk.END)
            self.sup_t_entry.insert(0, "SUPERVISOR DE TURNO")
            self.sup_c_entry.delete(0, tk.END)
            self.sup_c_entry.insert(0, "SUPERVISOR DE CAMARA")
            
            # Limpiar operadores
            self.operadores.clear()
            self.operadores_widgets.clear()
            self.next_op_code = 1
            self._refrescar_operadores()
            self._agregar_operador()  # Agregar uno por defecto
            
            # Limpiar descripción de relevo
            self.shift_text.delete("1.0", tk.END)
            
            # Limpiar tablas
            self._limpiar_todas_las_tablas()
            
            self.show_message("✅ Datos Limpiados", 
                            "Todos los datos de distribución han sido limpiados.", 
                            "info")

    def _limpiar_todas_las_tablas(self):
        """Limpia todas las tablas de distribución."""
        # Limpiar personal
        for item in self.personal_data:
            item["conductor"] = ""
            item["operador"] = ""
        
        # Limpiar motorizados
        self.motorizados_data.clear()
        
        # Limpiar sierra bravos
        self.sierra_bravos_data.clear()
        
        # Limpiar bases operativas
        for item in self.bases_operativas_data:
            item["serenos"] = ""
        
        # Limpiar prevención
        for item in self.prevencion_data:
            item["serenos"] = ""
        
        # Actualizar todas las tablas
        self._actualizar_tabla_personal()
        self._actualizar_tabla_motorizados()
        self._actualizar_tabla_sierra_bravos()
        self._actualizar_tabla_bases_operativas()
        self._actualizar_tabla_prevencion()

    def _imprimir_distribucion(self):
        """Imprime o genera reporte de distribución de personal."""
        try:
            # Crear contenido del reporte
            reporte_content = self._generar_contenido_reporte()
            
            # Guardar como archivo temporal
            import tempfile
            import os
            
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', 
                                                   delete=False, encoding='utf-8')
            temp_file.write(reporte_content)
            temp_file.close()
            
            # Intentar imprimir
            try:
                import subprocess
                import platform
                
                if platform.system() == "Windows":
                    os.startfile(temp_file.name, "print")
                else:
                    subprocess.run(['lpr', temp_file.name])
                
                self.show_message("🖨️ Impresión Enviada", 
                                "El reporte de distribución ha sido enviado a la impresora.", 
                                "info")
                
            except Exception as e:
                # Si no se puede imprimir, mostrar el contenido
                self._mostrar_reporte_ventana(reporte_content)
            
            # Limpiar archivo temporal después de un tiempo
            import threading
            def cleanup_temp_file():
                import time
                time.sleep(5)  # Esperar 5 segundos
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
            
            threading.Thread(target=cleanup_temp_file, daemon=True).start()
            
        except Exception as e:
            self.show_message("❌ Error al Imprimir", 
                            f"No se pudo generar el reporte:\n{str(e)}", 
                            "error")

    def mostrar_opciones_wialon(self):
        """Muestra una ventana emergente premium con opciones para Wialon."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Opciones Wialon")
        dialog.geometry("650x470")
        dialog.minsize(580, 430)
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.configure(bg='white')
        try:
            dialog.grab_set()
        except Exception:
            pass
        
        dialog.update_idletasks()
        screen_w = dialog.winfo_screenwidth()
        screen_h = dialog.winfo_screenheight()
        win_w, win_h = 650, 470
        x = (screen_w // 2) - (win_w // 2)
        y = (screen_h // 2) - (win_h // 2)
        dialog.geometry(f'{win_w}x{win_h}+{x}+{y}')
        
        main_frame = tk.Frame(dialog, bg='white', padx=30, pady=24)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(main_frame, text="🛰️ Gestión de Wialon", 
                 font=('Segoe UI', 16, 'bold'), bg='white', fg='#2c3e50').pack(pady=(0, 6))
        
        tk.Label(main_frame, text="Seleccione una acción para las unidades:", 
                 font=('Segoe UI', 11), bg='white', fg='#7f8c8d').pack(pady=(0, 18))
        
        btn_frame = tk.Frame(main_frame, bg='white')
        btn_frame.pack(fill=tk.X)
        
        btn_url = ttk.Button(btn_frame, text="🌐 WIALON URL  —  Abrir Monitor", 
                            command=lambda: [dialog.destroy(), self.controller.abrir_url_wialon()],
                            style='Accent.TButton')
        btn_url.pack(fill=tk.X, pady=8, ipady=8)
        
        btn_km_ap = ttk.Button(btn_frame, text="📏 WIALON KM  —  Tiempo Real (descuento 4-5 km)", 
                           command=lambda: [dialog.destroy(), self.controller.consultar_km_wialon()],
                           style='Success.TButton')
        btn_km_ap.pack(fill=tk.X, pady=8, ipady=8)
        
        btn_ap = ttk.Button(
            btn_frame,
            text="📌 WIALON A.P.  —  Geocercas NORTE / CENTRO / SUR / ENACE",
            command=lambda: [dialog.destroy(), self.controller.consultar_ap_wialon()],
            style='Accent.TButton'
        )
        btn_ap.pack(fill=tk.X, pady=8, ipady=8)
        
        self.create_tooltip(
            btn_ap,
            "Cálculo de Auxilio Público (A.P.)\n"
            "────────────────────────────\n"
            "• Extrae cronologías de estacionamiento del reporte\n"
            "• Suma SOLO minutos dentro de geocercas permitidas\n"
            "• Redondea a bloques de 5 minutos\n"
            "• Aplica descuento de 45 min por unidad"
        )
        
        tk.Frame(btn_frame, height=2, bg='#ecf0f1').pack(fill=tk.X, pady=(18, 12))
        
        btn_cerrar = tk.Button(
            btn_frame, text="✕  CERRAR VENTANA", 
            command=dialog.destroy,
            bg='#e74c3c', fg='white', 
            font=('Segoe UI', 11, 'bold'),
            relief='flat', cursor='hand2',
            activebackground='#c0392b',
            activeforeground='white',
            bd=0,
            padx=16, pady=4
        )
        btn_cerrar.pack(fill=tk.X, pady=(6, 0), ipady=8)




    def _generar_contenido_reporte(self):
        """Genera el contenido del reporte de distribución."""
        fecha_actual = time.strftime("%d/%m/%Y %H:%M:%S")
        
        reporte = f"""
{'='*80}
                    DISTRIBUCIÓN DE PERSONAL - SERENAZGO
{'='*80}
Fecha de Generación: {fecha_actual}

👤 SUPERVISORES:
{'='*40}
• Supervisor (T): {self.sup_t_entry.get()}
• Supervisor (C): {self.sup_c_entry.get()}

📹 OPERADORES DE CÁMARAS:
{'='*40}
"""
        
        for operador in self.operadores:
            reporte += f"• {operador['nombre']} (Código: {operador['op_code']})\n"
        
        reporte += f"""
📝 DESCRIPCIÓN DE RELEVO DE TURNO:
{'='*40}
{self.shift_text.get("1.0", tk.END).strip()}

🚔 UNIDADES EN CAMPO:
{'='*40}
"""
        
        for item in self.personal_data:
            if item["conductor"] or item["operador"]:
                reporte += f"• {item['unidad']}: {item['conductor']} / {item['operador']}\n"
        
        reporte += f"""
🏍️ MOTORIZADOS:
{'='*40}
"""
        
        for item in self.motorizados_data:
            reporte += f"• {item['unidad']}: {item['conductor']}\n"
        
        reporte += f"""
👥 SIERRA BRAVOS:
{'='*40}
"""
        
        for item in self.sierra_bravos_data:
            reporte += f"• {item['id']}: {item['a_pie']}\n"
        
        reporte += f"""
🏢 BASES OPERATIVAS:
{'='*40}
"""
        
        for item in self.bases_operativas_data:
            if item["serenos"]:
                reporte += f"• {item['id']}: {item['serenos']}\n"
        
        reporte += f"""
🛡️ PREVENCIÓN:
{'='*40}
"""
        
        for item in self.prevencion_data:
            if item["serenos"]:
                reporte += f"• {item['id']}: {item['serenos']}\n"
        
        reporte += f"""
{'='*80}
        Fin del Reporte - Sistema de Monitoreo Serenazgo
{'='*80}
"""
        
        return reporte

    def _mostrar_reporte_ventana(self, contenido):
        """Muestra el reporte en una ventana emergente."""
        reporte_window = tk.Toplevel(self.root)
        reporte_window.title("📋 Reporte de Distribución de Personal")
        reporte_window.geometry("800x600")
        reporte_window.configure(bg=self.COLOR_FONDO)
        reporte_window.attributes('-topmost', True)
        
        # Frame principal
        main_frame = tk.Frame(reporte_window, bg=self.COLOR_FONDO)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(main_frame, text="📋 REPORTE DE DISTRIBUCIÓN", 
                              font=self.font_titulo, bg=self.COLOR_FONDO, fg=self.COLOR_HEADER)
        title_label.pack(pady=(0, 20))
        
        # Text widget con scrollbar
        text_frame = tk.Frame(main_frame, bg=self.COLOR_FONDO)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, font=('Consolas', 10), 
                             bg='white', fg='black', wrap=tk.NONE)
        scrollbar_y = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        scrollbar_x = ttk.Scrollbar(text_frame, orient="horizontal", command=text_widget.xview)
        
        text_widget.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Insertar contenido
        text_widget.insert(tk.END, contenido)
        text_widget.config(state=tk.DISABLED)
        
        # Botón cerrar
        ttk.Button(main_frame, text="Cerrar", 
                  command=reporte_window.destroy).pack(pady=(20, 0))
        
        self.register_child_window(reporte_window)

    def _agregar_operador(self):
        """Agrega un nuevo operador a la lista."""
        op_code = f"{self.next_op_code:02d}"
        self.next_op_code += 1
        operador = {"nombre": "", "op_code": op_code}
        self.operadores.append(operador)
        self._refrescar_operadores()

    def _eliminar_operador(self, idx):
        """Elimina un operador de la lista."""
        if 0 <= idx < len(self.operadores):
            self.operadores.pop(idx)
            self._refrescar_operadores()
        if not self.operadores:
            self.next_op_code = 1

    def _refrescar_operadores(self):
        """Refresca la lista visual de operadores."""
        for widgets in self.operadores_widgets:
            for w in widgets:
                w.destroy()
        self.operadores_widgets.clear()
        
        for i, operador in enumerate(self.operadores):
            entry_nombre = tk.Entry(self.operadores_list_frame, font=self.font_base)
            entry_nombre.insert(0, operador["nombre"])
            entry_nombre.grid(row=i, column=0, sticky="ew", pady=2)
            entry_nombre.bind("<KeyRelease>", lambda e, idx=i: self._actualizar_nombre_operador(idx, e.widget.get()))
            
            label_op_code = tk.Label(self.operadores_list_frame, text=f"Código OP:", font=self.font_base)
            label_op_code.grid(row=i, column=1, padx=(5, 0))
            
            entry_op_code = tk.Entry(self.operadores_list_frame, font=self.font_base, width=5)
            entry_op_code.insert(0, operador["op_code"])
            entry_op_code.grid(row=i, column=2, padx=(0, 5))
            entry_op_code.bind("<KeyRelease>", lambda e, idx=i: self._actualizar_op_code_operador(idx, e.widget.get()))
            
            btn_eliminar = tk.Button(self.operadores_list_frame, text="🗑️", font=self.font_base, 
                                   command=lambda idx=i: self._eliminar_operador(idx))
            btn_eliminar.grid(row=i, column=3, padx=(5, 0), pady=2)
            
            self.operadores_widgets.append([entry_nombre, label_op_code, entry_op_code, btn_eliminar])
        
        self.operadores_list_frame.grid_columnconfigure(0, weight=1)

    def _actualizar_nombre_operador(self, idx, nuevo_nombre):
        """Actualiza el nombre de un operador."""
        if 0 <= idx < len(self.operadores):
            self.operadores[idx]["nombre"] = nuevo_nombre

    def _actualizar_op_code_operador(self, idx, nuevo_op_code):
        """Actualiza el código de un operador."""
        if 0 <= idx < len(self.operadores):
            self.operadores[idx]["op_code"] = nuevo_op_code

    def _crear_tabla_personal(self, parent):
        """Crea la tabla de personal."""
        from tkinter import ttk
        
        # Título descriptivo
        label_titulo = tk.Label(parent, text="🚓 UNIDADES EN CAMPO", font=("Segoe UI", 13, "bold"), 
                               bg=self.COLOR_FONDO, fg=self.COLOR_HEADER, pady=8)
        label_titulo.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        # Datos iniciales
        self.personal_data = [
            {"unidad": "EUI-621", "conductor": "VARGAS ROJAS GEANCARLO", "operador": "OLIVOS LEON MARCELO"},
            {"unidad": "EUI-682", "conductor": "MENDOZA JARA VICTOR", "operador": "ECHE VILELA MARCO"},
            {"unidad": "EUI-683", "conductor": "CHUNGA ADRIANZEN RODOLFO", "operador": "JIMENEZ GARCES JORGE"},
            {"unidad": "EUI-646", "conductor": "VIDAL TEMOCHE MARTIN", "operador": "CHIROQUE PEREZ LENNY"},
            {"unidad": "EUI-685", "conductor": "ASANZA HUANCAS FELIX", "operador": "RONDOY CRUZ PABLO"},
            {"unidad": "EUI-679", "conductor": "MOGOLLON AGUILAR PERCY", "operador": "CRUZ INFANTE INGRID"},
            {"unidad": "EUI-680", "conductor": "MACALUPU AYALA ROSENDO", "operador": "JIMENEZ GARCES NANCY"},
            {"unidad": "EUI-645", "conductor": "FLORES RUIZ JOSE", "operador": "ATOCHE ORDINOLA ESTEBAN"},
            {"unidad": "EUI-647", "conductor": "RONDOY LOPEZ GROVER", "operador": "MONASTERIO RODRIGUEZ HENRY"},
            {"unidad": "EUI-668", "conductor": "VIVAS FARRO CARLOS", "operador": "MEDINA QUEVEDO JAVIER"},
        ]
        
        # Frame para tabla
        table_frame = tk.Frame(parent, bg=self.COLOR_FONDO)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("unidad", "conductor", "operador")
        self.tree_personal = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        self.tree_personal.heading("unidad", text="🚔 Unidad")
        self.tree_personal.heading("conductor", text="👨‍✈️ Conductor")
        self.tree_personal.heading("operador", text="🧑‍✈️ Operador")
        self.tree_personal.column("unidad", width=100, anchor="center")
        self.tree_personal.column("conductor", width=220, anchor="w")
        self.tree_personal.column("operador", width=220, anchor="w")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree_personal.yview)
        self.tree_personal.configure(yscrollcommand=scrollbar.set)
        self.tree_personal.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self._actualizar_tabla_personal()
        self.tree_personal.bind('<Double-1>', self._editar_celda_personal)
        self._entry_editor = None
        self._editing_info = None

    def _actualizar_tabla_personal(self):
        """Actualiza la tabla de personal según el filtro activo."""
        for row in self.tree_personal.get_children():
            self.tree_personal.delete(row)
        
        filtro = self.get_filtro_var()
        if filtro == "MANUAL":
            unidades_filtradas = [fila['alias'] for fila in self.fila_widgets_data if fila['var_chk'].get() and fila['alias'] in self.unidades_mostradas]
        else:
            unidades_filtradas = self.unidades_mostradas
        
        alias_map = {}
        if hasattr(self.controller, 'model') and hasattr(self.controller.model, 'ALIAS_UNIDADES'):
            for alias, codigo in self.controller.model.ALIAS_UNIDADES.items():
                alias_map[codigo] = alias
        
        for item in self.personal_data:
            alias_completo = alias_map.get(item["unidad"], item["unidad"])
            if alias_completo in unidades_filtradas:
                self.tree_personal.insert("", tk.END, values=(alias_completo, item["conductor"], item["operador"]))

    def _editar_celda_personal(self, event):
        """Permite editar celdas de la tabla de personal."""
        region = self.tree_personal.identify('region', event.x, event.y)
        if region != 'cell':
            return
        
        row_id = self.tree_personal.identify_row(event.y)
        col_id = self.tree_personal.identify_column(event.x)
        if not row_id or not col_id:
            return
        
        col_index = int(col_id.replace('#', '')) - 1
        columns = ("unidad", "conductor", "operador")
        col_name = columns[col_index]
        
        if col_name == "unidad":
            return
        
        x, y, width, height = self.tree_personal.bbox(row_id, col_id)
        valor_actual = self.tree_personal.set(row_id, col_name)
        
        if self._entry_editor:
            self._entry_editor.destroy()
        
        entry = tk.Entry(self.tree_personal, font=self.font_base)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, valor_actual)
        entry.focus_set()
        entry.select_range(0, tk.END)
        self._entry_editor = entry
        self._editing_info = (row_id, col_name)
        
        entry.bind('<Return>', lambda e: self._guardar_edicion_personal())
        entry.bind('<FocusOut>', lambda e: self._guardar_edicion_personal())

    def _guardar_edicion_personal(self):
        """Guarda la edición de una celda de personal."""
        if not self._entry_editor or not self._editing_info:
            return
        
        nuevo_valor = self._entry_editor.get()
        row_id, col_name = self._editing_info
        self.tree_personal.set(row_id, col_name, nuevo_valor)
        
        values = self.tree_personal.item(row_id, 'values')
        alias_val = values[0]
        
        codigo_unidad = None
        if hasattr(self.controller, 'model') and hasattr(self.controller.model, 'ALIAS_UNIDADES'):
            for alias, codigo in self.controller.model.ALIAS_UNIDADES.items():
                if alias == alias_val:
                    codigo_unidad = codigo
                    break
        
        if not codigo_unidad:
            codigo_unidad = alias_val
        
        for item in self.personal_data:
            if item["unidad"] == codigo_unidad:
                item[col_name] = nuevo_valor
                break
        
        self._entry_editor.destroy()
        self._entry_editor = None
        self._editing_info = None

    def _crear_tabla_motorizados(self, parent):
        """Crea la tabla de motorizados."""
        from tkinter import ttk
        
        label_titulo = tk.Label(parent, text="🏍️MOTORIZADOS", font=("Segoe UI", 13, "bold"), 
                               bg=self.COLOR_FONDO, fg=self.COLOR_HEADER, pady=8)
        label_titulo.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        self.motorizados_data = [
            {"unidad": "CAZ-02", "conductor": "LAZO GUERRERO PAUL"},
            {"unidad": "CAZ-03", "conductor": "OLAYA RIVERA MIGUEL"},
        ]
        
        table_frame = tk.Frame(parent, bg=self.COLOR_FONDO)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("unidad", "conductor")
        self.tree_motorizados = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        self.tree_motorizados.heading("unidad", text="🚔 Unidad")
        self.tree_motorizados.heading("conductor", text="👨‍✈️ Conductor")
        self.tree_motorizados.column("unidad", width=100, anchor="center")
        self.tree_motorizados.column("conductor", width=220, anchor="w")
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree_motorizados.yview)
        self.tree_motorizados.configure(yscrollcommand=scrollbar.set)
        self.tree_motorizados.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self._actualizar_tabla_motorizados()
        self.tree_motorizados.bind('<Double-1>', self._editar_celda_motorizados)
        self._motorizados_entry_editor = None
        self._motorizados_editing_info = None
        
        # Botones
        btn_frame = tk.Frame(parent, bg=self.COLOR_FONDO)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        btn_add = ttk.Button(btn_frame, text="Agregar Motorizado", command=self._agregar_motorizado)
        btn_add.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=2)
        
        btn_del = ttk.Button(btn_frame, text="Eliminar Seleccionado", command=self._eliminar_motorizado)
        btn_del.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=2)

    def _actualizar_tabla_motorizados(self):
        """Actualiza la tabla de motorizados."""
        for row in self.tree_motorizados.get_children():
            self.tree_motorizados.delete(row)
        for item in self.motorizados_data:
            self.tree_motorizados.insert("", tk.END, values=(item["unidad"], item["conductor"]))

    def _agregar_motorizado(self):
        """Agrega un nuevo motorizado."""
        usados = {item["unidad"] for item in self.motorizados_data}
        siguiente = None
        for i in range(1, 11):
            unidad = f"CAZ-{i:02d}"
            if unidad not in usados:
                siguiente = unidad
                break
        if siguiente is None:
            self.show_message("Límite alcanzado", "Solo se permiten 10 motorizados.", "warning")
            return
        self.motorizados_data.append({"unidad": siguiente, "conductor": ""})
        self._actualizar_tabla_motorizados()

    def _eliminar_motorizado(self):
        """Elimina un motorizado seleccionado."""
        selected = self.tree_motorizados.selection()
        if not selected:
            self.show_message("Selecciona una fila", "Debes seleccionar una fila para eliminar.", "warning")
            return
        idx = self.tree_motorizados.index(selected[0])
        if 0 <= idx < len(self.motorizados_data):
            del self.motorizados_data[idx]
            self._actualizar_tabla_motorizados()

    def _editar_celda_motorizados(self, event):
        """Permite editar celdas de motorizados."""
        region = self.tree_motorizados.identify('region', event.x, event.y)
        if region != 'cell':
            return
        
        row_id = self.tree_motorizados.identify_row(event.y)
        col_id = self.tree_motorizados.identify_column(event.x)
        if not row_id or not col_id:
            return
        
        col_index = int(col_id.replace('#', '')) - 1
        columns = ("unidad", "conductor")
        col_name = columns[col_index]
        
        if col_name != "conductor":
            return
        
        x, y, width, height = self.tree_motorizados.bbox(row_id, col_id)
        valor_actual = self.tree_motorizados.set(row_id, col_name)
        
        if self._motorizados_entry_editor:
            self._motorizados_entry_editor.destroy()
        
        entry = tk.Entry(self.tree_motorizados, font=self.font_base)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, valor_actual)
        entry.focus_set()
        entry.select_range(0, tk.END)
        self._motorizados_entry_editor = entry
        self._motorizados_editing_info = (row_id, col_name)
        
        entry.bind('<Return>', lambda e: self._guardar_edicion_motorizados())
        entry.bind('<FocusOut>', lambda e: self._guardar_edicion_motorizados())

    def _guardar_edicion_motorizados(self):
        """Guarda la edición de motorizados."""
        if not self._motorizados_entry_editor or not self._motorizados_editing_info:
            return
        
        nuevo_valor = self._motorizados_entry_editor.get()
        row_id, col_name = self._motorizados_editing_info
        idx = self.tree_motorizados.index(row_id)
        if 0 <= idx < len(self.motorizados_data):
            self.motorizados_data[idx][col_name] = nuevo_valor
        self._actualizar_tabla_motorizados()
        self._motorizados_entry_editor.destroy()
        self._motorizados_entry_editor = None
        self._motorizados_editing_info = None

    def _crear_tabla_sierra_bravos(self, parent):
        """Crea la tabla de Sierra Bravos."""
        from tkinter import ttk
        
        label_titulo = tk.Label(parent, text="👮SIERRA BRAVOS", font=("Segoe UI", 13, "bold"), 
                               bg=self.COLOR_FONDO, fg=self.COLOR_HEADER, pady=8)
        label_titulo.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        self.sierra_bravos_data = [
            {"id": "SB-01", "a_pie": "ARANIBAR SANDOVAL HECTOR / SALCEDO CARBAJAL FERNANDO"},
            {"id": "SB-02", "a_pie": "VINCES SANCARRANCO JAVIER / CORREA FIESTAS PERCY"},
            {"id": "SB-03", "a_pie": "SALDARRIAGA CIENFUEGOS NAHELY / SANDOVAL FARIAS GLORIA"},
        ]
        
        table_frame = tk.Frame(parent, bg=self.COLOR_FONDO)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("id", "a_pie")
        self.tree_sierra_bravos = ttk.Treeview(table_frame, columns=columns, show="headings", height=7)
        self.tree_sierra_bravos.heading("id", text="ID")
        self.tree_sierra_bravos.heading("a_pie", text="A Pie")
        self.tree_sierra_bravos.column("id", width=80, anchor="center")
        self.tree_sierra_bravos.column("a_pie", width=400, anchor="w")
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree_sierra_bravos.yview)
        self.tree_sierra_bravos.configure(yscrollcommand=scrollbar.set)
        self.tree_sierra_bravos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self._actualizar_tabla_sierra_bravos()
        self.tree_sierra_bravos.bind('<Double-1>', self._editar_celda_sierra_bravos)
        self._sierra_bravos_entry_editor = None
        self._sierra_bravos_editing_info = None
        
        # Botones
        btn_frame = tk.Frame(parent, bg=self.COLOR_FONDO)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        btn_add = ttk.Button(btn_frame, text="Agregar", command=self._agregar_sierra_bravos)
        btn_add.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=2)
        
        btn_del = ttk.Button(btn_frame, text="Eliminar Seleccionado", command=self._eliminar_sierra_bravos)
        btn_del.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=2)

    def _actualizar_tabla_sierra_bravos(self):
        """Actualiza la tabla de Sierra Bravos."""
        for row in self.tree_sierra_bravos.get_children():
            self.tree_sierra_bravos.delete(row)
        for item in self.sierra_bravos_data:
            self.tree_sierra_bravos.insert("", tk.END, values=(item["id"], item["a_pie"]))

    def _agregar_sierra_bravos(self):
        """Agrega un nuevo Sierra Bravo."""
        usados = {item["id"] for item in self.sierra_bravos_data}
        siguiente = None
        for i in range(1, 11):
            id_sb = f"SB-{i:02d}"
            if id_sb not in usados:
                siguiente = id_sb
                break
        if siguiente is None:
            self.show_message("Límite alcanzado", "Solo se permiten 10 Sierra Bravos.", "warning")
            return
        self.sierra_bravos_data.append({"id": siguiente, "a_pie": ""})
        self._actualizar_tabla_sierra_bravos()

    def _eliminar_sierra_bravos(self):
        """Elimina un Sierra Bravo seleccionado."""
        selected = self.tree_sierra_bravos.selection()
        if not selected:
            self.show_message("Selecciona una fila", "Debes seleccionar una fila para eliminar.", "warning")
            return
        idx = self.tree_sierra_bravos.index(selected[0])
        if 0 <= idx < len(self.sierra_bravos_data):
            del self.sierra_bravos_data[idx]
            self._actualizar_tabla_sierra_bravos()

    def _editar_celda_sierra_bravos(self, event):
        """Permite editar celdas de Sierra Bravos."""
        region = self.tree_sierra_bravos.identify('region', event.x, event.y)
        if region != 'cell':
            return
        
        row_id = self.tree_sierra_bravos.identify_row(event.y)
        col_id = self.tree_sierra_bravos.identify_column(event.x)
        if not row_id or not col_id:
            return
        
        col_index = int(col_id.replace('#', '')) - 1
        columns = ("id", "a_pie")
        col_name = columns[col_index]
        
        if col_name != "a_pie":
            return
        
        x, y, width, height = self.tree_sierra_bravos.bbox(row_id, col_id)
        valor_actual = self.tree_sierra_bravos.set(row_id, col_name)
        
        if self._sierra_bravos_entry_editor:
            self._sierra_bravos_entry_editor.destroy()
        
        entry = tk.Entry(self.tree_sierra_bravos, font=self.font_base, justify='left')
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, valor_actual)
        entry.focus_set()
        entry.select_range(0, tk.END)
        self._sierra_bravos_entry_editor = entry
        self._sierra_bravos_editing_info = (row_id, col_name)
        
        entry.bind('<Return>', lambda e: self._guardar_edicion_sierra_bravos())
        entry.bind('<FocusOut>', lambda e: self._guardar_edicion_sierra_bravos())

    def _guardar_edicion_sierra_bravos(self):
        """Guarda la edición de Sierra Bravos."""
        if not self._sierra_bravos_entry_editor or not self._sierra_bravos_editing_info:
            return
        
        nuevo_valor = self._sierra_bravos_entry_editor.get()
        row_id, col_name = self._sierra_bravos_editing_info
        idx = self.tree_sierra_bravos.index(row_id)
        if 0 <= idx < len(self.sierra_bravos_data):
            self.sierra_bravos_data[idx][col_name] = nuevo_valor
        self._actualizar_tabla_sierra_bravos()
        self._sierra_bravos_entry_editor.destroy()
        self._sierra_bravos_entry_editor = None
        self._sierra_bravos_editing_info = None

    def _crear_tabla_bases_operativas(self, parent):
        """Crea la tabla de Bases Operativas."""
        from tkinter import ttk
        
        label_titulo = tk.Label(parent, text="🏢BASES OPERATIVAS", font=("Segoe UI", 13, "bold"), 
                               bg=self.COLOR_FONDO, fg=self.COLOR_HEADER, pady=8)
        label_titulo.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        self.bases_operativas_data = [
            {"id": "CECOM CENTRO", "serenos": "ECA IMAN MAGUIN"},
            {"id": "CECOM NORTE", "serenos": "CORONADO ANGELDONIS MARCOS"},
            {"id": "CECOM ENACE", "serenos": "YACILA GUEVARA JULIO"},
        ]
        
        table_frame = tk.Frame(parent, bg=self.COLOR_FONDO)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("id", "serenos")
        self.tree_bases_operativas = ttk.Treeview(table_frame, columns=columns, show="headings", height=7)
        self.tree_bases_operativas.heading("id", text="ID")
        self.tree_bases_operativas.heading("serenos", text="Serenos")
        self.tree_bases_operativas.column("id", width=150, anchor="center")
        self.tree_bases_operativas.column("serenos", width=350, anchor="w")
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree_bases_operativas.yview)
        self.tree_bases_operativas.configure(yscrollcommand=scrollbar.set)
        self.tree_bases_operativas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self._actualizar_tabla_bases_operativas()
        self.tree_bases_operativas.bind('<Double-1>', self._editar_celda_bases_operativas)
        self._bases_operativas_entry_editor = None
        self._bases_operativas_editing_info = None
        
        # Botones
        btn_frame = tk.Frame(parent, bg=self.COLOR_FONDO)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        btn_add = ttk.Button(btn_frame, text="Agregar", command=self._agregar_base_operativa)
        btn_add.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=2)
        
        btn_del = ttk.Button(btn_frame, text="Eliminar Seleccionado", command=self._eliminar_base_operativa)
        btn_del.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=2)

    def _actualizar_tabla_bases_operativas(self):
        """Actualiza la tabla de bases operativas."""
        for row in self.tree_bases_operativas.get_children():
            self.tree_bases_operativas.delete(row)
        for item in self.bases_operativas_data:
            self.tree_bases_operativas.insert("", tk.END, values=(item["id"], item["serenos"]))

    def _agregar_base_operativa(self):
        """Agrega una nueva base operativa."""
        posibles_ids = ["CECOM CENTRO", "CECOM NORTE", "CECOM SUR", "CECOM ENACE"]
        usados = {item["id"] for item in self.bases_operativas_data}
        siguiente = None
        
        for id_base in posibles_ids:
            if id_base not in usados:
                siguiente = id_base
                break
        
        if siguiente is None:
            self.show_message("Límite alcanzado", "Ya se han agregado todas las bases operativas disponibles.", "warning")
            return
        
        self.bases_operativas_data.append({"id": siguiente, "serenos": ""})
        self._actualizar_tabla_bases_operativas()

    def _eliminar_base_operativa(self):
        """Elimina una base operativa seleccionada."""
        selected = self.tree_bases_operativas.selection()
        if not selected:
            self.show_message("Selecciona una fila", "Debes seleccionar una fila para eliminar.", "warning")
            return
        
        idx = self.tree_bases_operativas.index(selected[0])
        if 0 <= idx < len(self.bases_operativas_data):
            del self.bases_operativas_data[idx]
            self._actualizar_tabla_bases_operativas()

    def _editar_celda_bases_operativas(self, event):
        """Permite editar celdas de bases operativas."""
        region = self.tree_bases_operativas.identify('region', event.x, event.y)
        if region != 'cell':
            return
        
        row_id = self.tree_bases_operativas.identify_row(event.y)
        col_id = self.tree_bases_operativas.identify_column(event.x)
        if not row_id or not col_id:
            return
        
        col_index = int(col_id.replace('#', '')) - 1
        columns = ("id", "serenos")
        col_name = columns[col_index]
        
        if col_name != "serenos":
            return
        
        x, y, width, height = self.tree_bases_operativas.bbox(row_id, col_id)
        valor_actual = self.tree_bases_operativas.set(row_id, col_name)
        
        if self._bases_operativas_entry_editor:
            self._bases_operativas_entry_editor.destroy()
        
        entry = tk.Entry(self.tree_bases_operativas, font=self.font_base, justify='left')
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, valor_actual)
        entry.focus_set()
        entry.select_range(0, tk.END)
        self._bases_operativas_entry_editor = entry
        self._bases_operativas_editing_info = (row_id, col_name)
        
        entry.bind('<Return>', lambda e: self._guardar_edicion_bases_operativas())
        entry.bind('<FocusOut>', lambda e: self._guardar_edicion_bases_operativas())

    def _guardar_edicion_bases_operativas(self):
        """Guarda la edición de bases operativas."""
        if not self._bases_operativas_entry_editor or not self._bases_operativas_editing_info:
            return
        
        nuevo_valor = self._bases_operativas_entry_editor.get()
        row_id, col_name = self._bases_operativas_editing_info
        idx = self.tree_bases_operativas.index(row_id)
        
        if 0 <= idx < len(self.bases_operativas_data):
            self.bases_operativas_data[idx][col_name] = nuevo_valor
        
        self._actualizar_tabla_bases_operativas()
        self._bases_operativas_entry_editor.destroy()
        self._bases_operativas_entry_editor = None
        self._bases_operativas_editing_info = None

    def _crear_tabla_prevencion(self, parent):
        """Crea la tabla de Prevención."""
        from tkinter import ttk
        
        label_titulo = tk.Label(parent, text="🛡️PREVENCIÓN", font=("Segoe UI", 13, "bold"), 
                               bg=self.COLOR_FONDO, fg=self.COLOR_HEADER, pady=8)
        label_titulo.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        self.prevencion_data = [
            {"id": "PREVENCION NORTE", "serenos": "BENITES ZARATE GLADYS"},
            {"id": "PREVENCION SUR", "serenos": "AYALA PARDO PEDRO"},
        ]
        
        table_frame = tk.Frame(parent, bg=self.COLOR_FONDO)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("id", "serenos")
        self.tree_prevencion = ttk.Treeview(table_frame, columns=columns, show="headings", height=7)
        self.tree_prevencion.heading("id", text="ID")
        self.tree_prevencion.heading("serenos", text="Serenos")
        self.tree_prevencion.column("id", width=150, anchor="center")
        self.tree_prevencion.column("serenos", width=350, anchor="w")
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree_prevencion.yview)
        self.tree_prevencion.configure(yscrollcommand=scrollbar.set)
        self.tree_prevencion.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self._actualizar_tabla_prevencion()
        self.tree_prevencion.bind('<Double-1>', self._editar_celda_prevencion)
        self._prevencion_entry_editor = None
        self._prevencion_editing_info = None
        
        # Botones
        btn_frame = tk.Frame(parent, bg=self.COLOR_FONDO)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        btn_add = ttk.Button(btn_frame, text="Agregar", command=self._agregar_prevencion)
        btn_add.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=2)
        
        btn_del = ttk.Button(btn_frame, text="Eliminar Seleccionado", command=self._eliminar_prevencion)
        btn_del.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=2)

    def _actualizar_tabla_prevencion(self):
        """Actualiza la tabla de prevención."""
        for row in self.tree_prevencion.get_children():
            self.tree_prevencion.delete(row)
        for item in self.prevencion_data:
            self.tree_prevencion.insert("", tk.END, values=(item["id"], item["serenos"]))

    def _agregar_prevencion(self):
        """Agrega una nueva prevención."""
        posibles_ids = ["PREVENCION NORTE", "PREVENCION SUR", "PREVENCION CENTRO", "PREVENCION ENACE"]
        usados = {item["id"] for item in self.prevencion_data}
        siguiente = None
        
        for id_prevencion in posibles_ids:
            if id_prevencion not in usados:
                siguiente = id_prevencion
                break
        
        if siguiente is None:
            self.show_message("Límite alcanzado", "Ya se han agregado todas las prevenciones disponibles.", "warning")
            return
        
        self.prevencion_data.append({"id": siguiente, "serenos": ""})
        self._actualizar_tabla_prevencion()

    def _eliminar_prevencion(self):
        """Elimina una prevención seleccionada."""
        selected = self.tree_prevencion.selection()
        if not selected:
            self.show_message("Selecciona una fila", "Debes seleccionar una fila para eliminar.", "warning")
            return
        
        idx = self.tree_prevencion.index(selected[0])
        if 0 <= idx < len(self.prevencion_data):
            del self.prevencion_data[idx]
            self._actualizar_tabla_prevencion()

    def _editar_celda_prevencion(self, event):
        """Permite editar celdas de prevención."""
        region = self.tree_prevencion.identify('region', event.x, event.y)
        if region != 'cell':
            return
        
        row_id = self.tree_prevencion.identify_row(event.y)
        col_id = self.tree_prevencion.identify_column(event.x)
        if not row_id or not col_id:
            return
        
        col_index = int(col_id.replace('#', '')) - 1
        columns = ("id", "serenos")
        col_name = columns[col_index]
        
        if col_name != "serenos":
            return
        
        x, y, width, height = self.tree_prevencion.bbox(row_id, col_id)
        valor_actual = self.tree_prevencion.set(row_id, col_name)
        
        if self._prevencion_entry_editor:
            self._prevencion_entry_editor.destroy()
        
        entry = tk.Entry(self.tree_prevencion, font=self.font_base, justify='left')
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, valor_actual)
        entry.focus_set()
        entry.select_range(0, tk.END)
        self._prevencion_entry_editor = entry
        self._prevencion_editing_info = (row_id, col_name)
        
        entry.bind('<Return>', lambda e: self._guardar_edicion_prevencion())
        entry.bind('<FocusOut>', lambda e: self._guardar_edicion_prevencion())

    def _guardar_edicion_prevencion(self):
        """Guarda la edición de prevención."""
        if not self._prevencion_entry_editor or not self._prevencion_editing_info:
            return
        
        nuevo_valor = self._prevencion_entry_editor.get()
        row_id, col_name = self._prevencion_editing_info
        idx = self.tree_prevencion.index(row_id)
        
        if 0 <= idx < len(self.prevencion_data):
            self.prevencion_data[idx][col_name] = nuevo_valor
        
        self._actualizar_tabla_prevencion()
        self._prevencion_entry_editor.destroy()
        self._prevencion_entry_editor = None
        self._prevencion_editing_info = None

    def abrir_lista_camaras(self):
        """Abre la ventana de lista de cámaras."""
        ListaCamarasWindow(self.root, self.turno_var.get())


class ListaCamarasWindow:
    """Ventana para gestionar lista de cámaras con autocompletado nativo y validación oficial."""
    _window_open = False
    
    def __init__(self, parent, turno=None):
        if ListaCamarasWindow._window_open:
            from utils import ToastNotification
            ToastNotification(parent, "⚠️ La ventana de Lista de Cámaras ya está abierta 📹", 2000)
            return
        self.parent = parent
        self.turno = turno or "DÍA"
        self.camaras_seleccionadas = []
        self.window = None
        
        # Paleta de colores Premium
        self.COLOR_FONDO = "#f8f9fa"
        self.COLOR_HEADER = "#2c3e50"
        self.COLOR_ACCENT = "#3498db"
        self.COLOR_SUCCESS = "#27ae60"
        self.COLOR_DANGER = "#e74c3c"
        self.COLOR_TEXT_PR = "#2c3e50"
        self.COLOR_TEXT_SEC = "#7f8c8d"

        from report_ocurrencias import CAMARAS_LISTA
        self.camaras_disponibles = sorted(CAMARAS_LISTA)
        
        self.create_window()
        ListaCamarasWindow._window_open = True
    
    def create_window(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("📹 Panel de Control de Cámaras")
        self.window.geometry("700x750")
        self.window.configure(bg=self.COLOR_FONDO)
        self.window.resizable(False, False)
        
        # Colocar al frente una única vez al abrir
        self.window.attributes('-topmost', True)
        self.window.after(500, lambda: self.window.attributes('-topmost', False))
        
        # Centrar Ventana
        w, h = 700, 750
        x = (self.window.winfo_screenwidth() // 2) - (w // 2)
        y = (self.window.winfo_screenheight() // 2) - (h // 2)
        self.window.geometry(f'{w}x{h}+{x}+{y}')

        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        self.window.bind('<Escape>', lambda e: self._on_close())
        self._create_widgets()

    def _create_widgets(self):
        # Encabezado
        header = tk.Frame(self.window, bg=self.COLOR_HEADER, height=75)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="📹 GESTIÓN DE CÁMARAS", 
                 font=("Segoe UI", 18, "bold"), fg="white", bg=self.COLOR_HEADER).pack(expand=True)
        
        # Contenedor con margen
        main = tk.Frame(self.window, bg=self.COLOR_FONDO, padx=30, pady=25)
        main.pack(fill=tk.BOTH, expand=True)

        # Sección de Ingreso
        lbl_ingreso = tk.Label(main, text="Buscar cámara por nombre:", 
                              font=("Segoe UI", 11, "bold"), bg=self.COLOR_FONDO, fg=self.COLOR_TEXT_PR)
        lbl_ingreso.pack(anchor=tk.W)
        
        entry_cnt = tk.Frame(main, bg=self.COLOR_FONDO)
        entry_cnt.pack(fill=tk.X, pady=(10, 5))

        # Campo de Texto con borde estilizado
        self.entry_camara = tk.Entry(entry_cnt, font=("Segoe UI", 12), relief="solid", bd=1,
                                   highlightthickness=1, highlightbackground="#bdc3c7", highlightcolor=self.COLOR_ACCENT)
        self.entry_camara.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 10))
        
        btn_add = tk.Button(entry_cnt, text="➕ AÑADIR", command=self._agregar_camara,
                           font=("Segoe UI", 10, "bold"), bg=self.COLOR_SUCCESS, fg="white", 
                           relief="flat", padx=20, cursor="hand2", activebackground="#219150", activeforeground="white")
        btn_add.pack(side=tk.RIGHT, fill=tk.Y)
        
        tk.Label(main, text="⚠️ Solo se permiten cámaras registradas oficialmente.", 
                 font=("Segoe UI", 8, "italic"), bg=self.COLOR_FONDO, fg=self.COLOR_TEXT_SEC).pack(anchor=tk.W, pady=(0, 20))

        # Sección de Tabla de Cámaras
        list_frame = tk.LabelFrame(main, text=" 📍 Cámaras en el Reporte Actual ", font=("Segoe UI", 10, "bold"), 
                                 bg=self.COLOR_FONDO, padx=10, pady=10, labelanchor="n")
        list_frame.pack(fill=tk.BOTH, expand=True)

        tree_cnt = tk.Frame(list_frame, bg="white")
        tree_cnt.pack(fill=tk.BOTH, expand=True)

        # Estilo de la tabla
        style = ttk.Style()
        style.configure("Custom.Treeview", font=("Segoe UI", 10), rowheight=28)
        
        self.tree = ttk.Treeview(tree_cnt, columns=("#", "Cámara"), show="headings", height=12, style="Custom.Treeview")
        self.tree.heading("#", text="N°")
        self.tree.heading("Cámara", text="UBICACIÓN SELECCIONADA")
        self.tree.column("#", width=40, anchor=tk.CENTER)
        self.tree.column("Cámara", width=500, anchor=tk.W)
        
        scroll = ttk.Scrollbar(tree_cnt, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Botonera Inferior
        footer = tk.Frame(main, bg=self.COLOR_FONDO)
        footer.pack(fill=tk.X, pady=(20, 0))

        tk.Button(footer, text="🗑️ QUITAR", command=self._quitar,
                  font=("Segoe UI", 10, "bold"), bg=self.COLOR_DANGER, fg="white", 
                  relief="flat", padx=15, pady=10, cursor="hand2").pack(side=tk.LEFT)
        
        tk.Button(footer, text="💾 GENERAR Y COPIAR LISTA", command=self._guardar,
                  font=("Segoe UI", 11, "bold"), bg=self.COLOR_ACCENT, fg="white", 
                  relief="flat", padx=30, pady=10, cursor="hand2").pack(side=tk.RIGHT)

        # CONFIGURACIÓN DEL AUTOCOMPLETADO INTEGRADO (Sin ventanas externas)
        self._setup_auto_nativo()
        self.entry_camara.focus_set()

    def _setup_auto_nativo(self):
        """Prepara el sistema de sugerencias integrado."""
        self.pop_frame = None
        self.lb_auto = None
        
        self.entry_camara.bind('<KeyRelease>', self._on_input_change)
        # El retraso permite que el clic en el listbox se procese antes de ocultar el frame
        self.entry_camara.bind('<FocusOut>', lambda e: self.window.after(300, self._hide_pop))
        self.entry_camara.bind('<Down>', self._on_key_down)
        self.entry_camara.bind('<Up>', self._on_key_up)
        self.entry_camara.bind('<Return>', lambda e: self._on_return_pressed())

    def _on_input_change(self, e):
        """Maneja el texto tipiado y muestra sugerencias."""
        if e.keysym in ['Down', 'Up', 'Return', 'Escape']: return
        
        txt = self.entry_camara.get().strip()
        if not txt: 
            self._hide_pop()
            return
            
        matches = [c for c in self.camaras_disponibles if txt.lower() in c.lower()]
        if matches: 
            self._show_pop(matches)
        else: 
            self._hide_pop()

    def _show_pop(self, items):
        """Muestra el frame de sugerencias integradas."""
        if not self.pop_frame:
            # Creamos el frame y listbox hijo directo de self.window para que use .place()
            self.pop_frame = tk.Frame(self.window, relief="solid", bd=1, bg="white")
            self.lb_auto = tk.Listbox(self.pop_frame, font=("Segoe UI", 11), 
                                     selectbackground=self.COLOR_ACCENT, selectforeground="white",
                                     relief="flat", borderwidth=0, highlightthickness=0)
            self.lb_auto.pack(fill=tk.BOTH, expand=True)
            self.lb_auto.bind('<ButtonRelease-1>', self._on_list_click)

        self.lb_auto.delete(0, tk.END)
        for i in items: self.lb_auto.insert(tk.END, i)
        
        # Posicionamiento absoluto dentro de la ventana (para simular un popup)
        # Obtenemos la posición relativa a la ventana ROOT del entry
        ex = self.entry_camara.winfo_x() + self.entry_camara.master.winfo_x()
        ey = self.entry_camara.winfo_y() + self.entry_camara.master.winfo_y() + self.entry_camara.winfo_height()
        ew = self.entry_camara.winfo_width()
        eh = min(200, len(items) * 28 + 2)
        
        self.pop_frame.place(x=ex, y=ey, width=ew, height=eh)
        self.pop_frame.lift() # Asegurar que esté encima de todo

    def _hide_pop(self):
        """Oculta el cuadro de sugerencias nativo."""
        if self.pop_frame: 
            self.pop_frame.place_forget()

    def _on_list_click(self, e):
        """Maneja el clic en un ítem de la lista."""
        if self.lb_auto.curselection():
            self._confirmar_seleccion(self.lb_auto.get(self.lb_auto.curselection()))

    def _on_return_pressed(self):
        """Maneja la tecla Enter según el estado del autocompletado."""
        if self.pop_frame and self.pop_frame.winfo_viewable() and self.lb_auto.curselection():
            self._confirmar_seleccion(self.lb_auto.get(self.lb_auto.curselection()))
        else: 
            self._agregar_camara()

    def _confirmar_seleccion(self, val):
        """Pone el valor seleccionado en el campo."""
        self.entry_camara.delete(0, tk.END)
        self.entry_camara.insert(0, val)
        self._hide_pop()
        self.entry_camara.focus_set()

    def _on_key_down(self, e):
        if self.pop_frame and self.pop_frame.winfo_viewable():
            current = self.lb_auto.curselection()
            idx = (current[0] + 1) % self.lb_auto.size() if current else 0
            self.lb_auto.selection_clear(0, tk.END)
            self.lb_auto.selection_set(idx)
            self.lb_auto.see(idx)
        return "break"

    def _on_key_up(self, e):
        if self.pop_frame and self.pop_frame.winfo_viewable():
            current = self.lb_auto.curselection()
            idx = (current[0] - 1) % self.lb_auto.size() if current else self.lb_auto.size()-1
            self.lb_auto.selection_clear(0, tk.END)
            self.lb_auto.selection_set(idx)
            self.lb_auto.see(idx)
        return "break"

    def _agregar_camara(self):
        """Agrega la cámara a la lista previa validación oficial."""
        val = self.entry_camara.get().strip()
        if not val: return
        
        match = next((c for c in self.camaras_disponibles if c.lower() == val.lower()), None)
        if not match:
            # El parent=self.window garantiza que el aviso no salga detrás
            tk.messagebox.showerror("⚠️ Validación de Cámara", 
                f"La ubicación '{val}' no es válida.\n\n"
                "Para evitar errores, elija una cámara de la lista de sugerencias.",
                parent=self.window)
            return
            
        if match in self.camaras_seleccionadas: return
        
        self.camaras_seleccionadas.append(match)
        self._sync_table()
        self.entry_camara.delete(0, tk.END)
        self._hide_pop()

    def _quitar(self):
        """Quita las cámaras seleccionadas en la tabla."""
        selection = self.tree.selection()
        if not selection: return
        
        for i in selection: 
            self.camaras_seleccionadas.remove(self.tree.item(i)['values'][1])
        self._sync_table()

    def _sync_table(self):
        """Sincroniza la visualización de la tabla."""
        for i in self.tree.get_children(): self.tree.delete(i)
        for i, c in enumerate(self.camaras_seleccionadas, 1):
            self.tree.insert("", tk.END, values=(i, c))

    def _guardar(self):
        """Genera el reporte, copia al portapapeles y se despide con un toast."""
        if not self.camaras_seleccionadas: return
        
        reporte = [f"📹 REPORTE DE CÁMARAS MONITORIZADAS | TURNO {self.turno}", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
        for i, c in enumerate(self.camaras_seleccionadas, 1): reporte.append(f"  {i}. {c}")
        
        import platform; from datetime import datetime
        reporte.extend(["", f"📅 Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
                        f"👤 Operador: {platform.node().upper()}"])
        
        texto_final = "\n".join(reporte)
        self.window.clipboard_clear()
        self.window.clipboard_append(texto_final)
        self.window.update()
        
        from utils import ToastNotification
        ToastNotification(self.parent, "📄 Listado copiado correctamente", 2000)
        self._on_close()

    def _on_close(self):
        """Cierra la ventana de forma segura."""
        ListaCamarasWindow._window_open = False
        if self.window: self.window.destroy()


