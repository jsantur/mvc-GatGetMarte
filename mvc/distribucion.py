#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: Distribución de Unidades
================================
Aplicación para gestionar la distribución de unidades, motorizados y bases con generación de registros.

Autor: Sistema de Optimización
Fecha: 2025-06-16
"""

import tkinter as tk
from tkinter import ttk
import pyperclip
from datetime import datetime
from typing import Dict, Any

from constants import UI_CONSTANTS, ToastNotification, should_show_unit

class DistribucionWindow:
    _window_open = False

    def __init__(self, parent: tk.Tk, unidades_data: Dict[str, Any]):
        if DistribucionWindow._window_open:
            if hasattr(self, 'window') and self.window.winfo_exists():
                self.window.deiconify()
                self.window.focus_force()
            return
        self.parent = parent
        self.unidades_data = unidades_data
        self.motorizados_vars = {}
        self.bases_vars = {}
        self.sierra_bravos_vars = {}
        self._create_window()
        DistribucionWindow._window_open = True

    def _create_window(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Distribución de Unidades - Sistema Serenazgo")
        self.window.geometry('1200x800')
        self.window.resizable(True, True)
        self.window.configure(bg=UI_CONSTANTS['COLORS']['background'])
        
        # Deshabilitar el botón de cerrar de la interfaz
        self.window.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Agregar binding para cerrar con Escape
        self.window.bind('<Escape>', lambda e: self._on_close())
        
        self._center_window()
        self.window.attributes('-topmost', True)
        
        # Configurar grid principal
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        
        self._create_header()
        self._create_main_layout()
        self.window.focus_force()
        self._update_preview()

    def _center_window(self):
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

    def _create_header(self):
        """Crea el encabezado con información del turno y título."""
        header = tk.Frame(self.window, bg=UI_CONSTANTS['COLORS']['primary'], height=80)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_columnconfigure(1, weight=1)
        
        # Título principal
        title_frame = tk.Frame(header, bg=UI_CONSTANTS['COLORS']['primary'])
        title_frame.grid(row=0, column=0, sticky="w", padx=20, pady=15)
        
        tk.Label(title_frame, text="🖥️ DISTRIBUCIÓN DE UNIDADES", 
                font=('Arial', 16, 'bold'), fg='white', 
                bg=UI_CONSTANTS['COLORS']['primary']).pack(side=tk.LEFT)
        
        # Información del turno
        info_frame = tk.Frame(header, bg=UI_CONSTANTS['COLORS']['primary'])
        info_frame.grid(row=0, column=1, sticky="e", padx=20, pady=15)
        
        turno = self.unidades_data.get('turno_actual', 'NOCHE')
        hora = datetime.now().strftime("%H:%M")
        fecha = datetime.now().strftime("%d/%m/%Y")
        
        # Información principal
        tk.Label(info_frame, text=f"⏱ {hora} | 🗓 {fecha} | 🌇 {turno}", 
                font=('Arial', 12), fg='white', 
                bg=UI_CONSTANTS['COLORS']['primary']).pack(side=tk.RIGHT)
        
        # Mensaje informativo sobre Escape
        tk.Label(info_frame, text="💡 Presiona ESC para cerrar", 
                font=('Arial', 9), fg='#FFD700', 
                bg=UI_CONSTANTS['COLORS']['primary']).pack(side=tk.RIGHT, padx=(0, 15))

    def _create_main_layout(self):
        """Crea el layout principal con distribución horizontal."""
        main_container = tk.Frame(self.window, bg=UI_CONSTANTS['COLORS']['background'])
        main_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        
        # Configurar grid del contenedor principal
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_columnconfigure(1, weight=1)
        
        # Panel izquierdo - Controles y selecciones
        left_panel = self._create_left_panel(main_container)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Panel derecho - Vista previa y acciones
        right_panel = self._create_right_panel(main_container)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

    def _create_left_panel(self, parent):
        """Crea el panel izquierdo con todas las secciones de selección."""
        left_frame = tk.Frame(parent, bg=UI_CONSTANTS['COLORS']['background'])
        left_frame.grid_rowconfigure(5, weight=1)

        # Sección de Unidades
        self._create_units_section(left_frame)
        
        # Sección de Motorizados
        self._create_motorizados_section(left_frame)
        
        # Sección de Sierra Bravos
        self._create_sierra_bravos_section(left_frame)
        
        # Sección de Bases
        self._create_bases_section(left_frame)
        
        return left_frame

    def _create_units_section(self, parent):
        """Crea la sección de unidades con diseño mejorado."""
        units_frame = ttk.LabelFrame(parent, text="🚓 UNIDADES DISPONIBLES", 
                                    style='Modern.TLabelframe', padding=15)
        units_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        
        # Contenedor con scroll para las unidades
        canvas = tk.Canvas(units_frame, height=120, bg=UI_CONSTANTS['COLORS']['card_bg'], 
                          highlightthickness=0)
        scrollbar = ttk.Scrollbar(units_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=UI_CONSTANTS['COLORS']['card_bg'])
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Organizar unidades en grid
        filtered_units = self._get_filtered_units()
        for i, unit in enumerate(filtered_units):
            row = i // 3
            col = i % 3
            
            unit_label = tk.Label(scrollable_frame, text=f"🚓 {unit}", 
                                 font=('Arial', 10), bg=UI_CONSTANTS['COLORS']['card_bg'],
                                 fg=UI_CONSTANTS['COLORS']['text_primary'], 
                                 relief="flat", padx=8, pady=4)
            unit_label.grid(row=row, column=col, sticky="ew", padx=5, pady=2)
        
        # Configurar columnas para distribución uniforme
        for i in range(3):
            scrollable_frame.grid_columnconfigure(i, weight=1)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _create_motorizados_section(self, parent):
        """Crea la sección de motorizados con diseño mejorado."""
        motorizados_frame = ttk.LabelFrame(parent, text="🏍️ MOTORIZADOS", 
                                          style='Modern.TLabelframe', padding=15)
        motorizados_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        
        # Contenedor para los checkboxes
        checkboxes_frame = tk.Frame(motorizados_frame, bg=UI_CONSTANTS['COLORS']['card_bg'])
        checkboxes_frame.pack(fill="x", expand=True)
        
        # Organizar en 4 columnas
        for i in range(1, 11):
            row = (i - 1) // 4
            col = (i - 1) % 4
            
            alias = f"CZ.{i:02d}"
            var = tk.BooleanVar(value=False)
            self.motorizados_vars[alias] = var
            
            checkbox = tk.Checkbutton(checkboxes_frame, text=alias, variable=var,
                                     font=('Arial', 10), bg=UI_CONSTANTS['COLORS']['card_bg'],
                                     activebackground=UI_CONSTANTS['COLORS']['card_bg'],
                                     fg=UI_CONSTANTS['COLORS']['text_primary'],
                                     selectcolor=UI_CONSTANTS['COLORS']['primary'],
                                     command=self._update_preview)
            checkbox.grid(row=row, column=col, sticky="w", padx=10, pady=5)
        
        # Configurar columnas para distribución uniforme
        for i in range(4):
            checkboxes_frame.grid_columnconfigure(i, weight=1)

    def _create_sierra_bravos_section(self, parent):
        """Crea la sección de Sierra Bravos con diseño mejorado."""
        sierra_bravos_frame = ttk.LabelFrame(parent, text="👮 SIERRA BRAVOS", 
                                            style='Modern.TLabelframe', padding=15)
        sierra_bravos_frame.grid(row=3, column=0, sticky="ew", pady=(0, 15))
        
        # Contenedor para los checkboxes
        checkboxes_frame = tk.Frame(sierra_bravos_frame, bg=UI_CONSTANTS['COLORS']['card_bg'])
        checkboxes_frame.pack(fill="x", expand=True)
        
        # Organizar en 3 columnas
        for i in range(1, 7):
            row = (i - 1) // 3
            col = (i - 1) % 3
            
            alias = f"SB.{i:02d}"
            var = tk.BooleanVar(value=False)
            self.sierra_bravos_vars[alias] = var
            
            checkbox = tk.Checkbutton(checkboxes_frame, text=alias, variable=var,
                                     font=('Arial', 10), bg=UI_CONSTANTS['COLORS']['card_bg'],
                                     activebackground=UI_CONSTANTS['COLORS']['card_bg'],
                                     fg=UI_CONSTANTS['COLORS']['text_primary'],
                                     selectcolor=UI_CONSTANTS['COLORS']['primary'],
                                     command=self._update_preview)
            checkbox.grid(row=row, column=col, sticky="w", padx=10, pady=5)
        
        # Configurar columnas para distribución uniforme
        for i in range(3):
            checkboxes_frame.grid_columnconfigure(i, weight=1)

    def _create_bases_section(self, parent):
        """Crea la sección de bases con diseño mejorado."""
        bases_frame = ttk.LabelFrame(parent, text="🏢 BASES OPERATIVAS", 
                                    style='Modern.TLabelframe', padding=15)
        bases_frame.grid(row=4, column=0, sticky="ew", pady=(0, 15))
        
        # Contenedor para los checkboxes
        checkboxes_frame = tk.Frame(bases_frame, bg=UI_CONSTANTS['COLORS']['card_bg'])
        checkboxes_frame.pack(fill="x", expand=True)
        
        # Organizar en 2 columnas
        for i, base in enumerate(["Tierra 1", "Tierra 4"]):
            var = tk.BooleanVar(value=False)
            self.bases_vars[base] = var
            
            checkbox = tk.Checkbutton(checkboxes_frame, text=base, variable=var,
                                     font=('Arial', 10), bg=UI_CONSTANTS['COLORS']['card_bg'],
                                     activebackground=UI_CONSTANTS['COLORS']['card_bg'],
                                     fg=UI_CONSTANTS['COLORS']['text_primary'],
                                     selectcolor=UI_CONSTANTS['COLORS']['primary'],
                                     command=self._update_preview)
            checkbox.grid(row=0, column=i, sticky="w", padx=20, pady=5)
        
        # Configurar columnas para distribución uniforme
        for i in range(2):
            checkboxes_frame.grid_columnconfigure(i, weight=1)

    def _create_right_panel(self, parent):
        """Crea el panel derecho con vista previa y acciones."""
        right_frame = tk.Frame(parent, bg=UI_CONSTANTS['COLORS']['background'])
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        # Sección de vista previa
        preview_frame = ttk.LabelFrame(right_frame, text="📄 VISTA PREVIA DEL REGISTRO", 
                                      style='Modern.TLabelframe', padding=15)
        preview_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 15))
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)
        
        # Área de texto con scroll
        text_frame = tk.Frame(preview_frame, bg='#f8f9fa')
        text_frame.grid(row=0, column=0, sticky="nsew")
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        
        self.resultado_text = tk.Text(text_frame, wrap=tk.WORD, 
                                     font=('Consolas', 10), bg='#f8f9fa',
                                     fg=UI_CONSTANTS['COLORS']['text_primary'], 
                                     padx=15, pady=15, state='disabled', 
                                     relief="flat", borderwidth=1,
                                     highlightbackground=UI_CONSTANTS['COLORS']['border'],
                                     highlightthickness=1)
        
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.resultado_text.yview)
        self.resultado_text.configure(yscrollcommand=scrollbar.set)
        
        self.resultado_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Sección de acciones
        actions_frame = tk.Frame(right_frame, bg=UI_CONSTANTS['COLORS']['background'])
        actions_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        # Configurar grid para distribución uniforme de botones
        actions_frame.grid_columnconfigure(0, weight=1)  # Botón Copiar
        actions_frame.grid_columnconfigure(1, weight=1)  # Botón Limpiar
        actions_frame.grid_columnconfigure(2, weight=1)  # Botón Cerrar
        
        # Configurar estilos uniformes con colores distintivos
        style = ttk.Style()
        
        # Estilo para botón Portapapeles (azul)
        style.configure('Uniform.Primary.TButton', 
                       font=('Segoe UI', 11, 'bold'),
                       padding=(15, 10),
                       width=15,
                       foreground='white',
                       background='#007bff')
        style.map('Uniform.Primary.TButton',
                 background=[('active', '#0056b3'), ('pressed', '#004085')])
        
        # Estilo para botón Limpiar (gris)
        style.configure('Uniform.Secondary.TButton', 
                       font=('Segoe UI', 11, 'bold'),
                       padding=(15, 10),
                       width=15,
                       foreground='white',
                       background='#6c757d')
        style.map('Uniform.Secondary.TButton',
                 background=[('active', '#545b62'), ('pressed', '#3d4449')])
        
        # Estilo para botón Cerrar (rojo)
        style.configure('Uniform.Danger.TButton', 
                       font=('Segoe UI', 11, 'bold'),
                       padding=(15, 10),
                       width=15,
                       foreground='white',
                       background='#dc3545')
        style.map('Uniform.Danger.TButton',
                 background=[('active', '#c82333'), ('pressed', '#a71e2a')])
        
        # Botón copiar
        copy_btn = ttk.Button(actions_frame, text="📋 Portapapeles", 
                             command=self._copy_report, style='Uniform.Primary.TButton')
        copy_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        # Botón limpiar
        clear_btn = ttk.Button(actions_frame, text="🗑️ Limpiar", 
                              command=self._clear_selection, style='Uniform.Secondary.TButton')
        clear_btn.grid(row=0, column=1, sticky="ew", padx=5)
        
        # Botón cerrar
        close_btn = ttk.Button(actions_frame, text="❌ Cerrar", 
                              command=self._on_close, style='Uniform.Danger.TButton')
        close_btn.grid(row=0, column=2, sticky="ew", padx=(5, 0))
        
        return right_frame

    def _get_filtered_units(self):
        return [unit for unit in self.unidades_data.get('unidades_disponibles', [])
                if should_show_unit(self.unidades_data, unit)]

    def _build_report_text(self):
        hora = datetime.now().strftime("%H:%M")
        fecha = datetime.now().strftime("%d/%m/%Y")
        turno = self.unidades_data.get('turno_actual', 'NOCHE')
        usuario = "OPERADOR12"

        # Diseño optimizado para móvil - formato vertical y compacto
        lines = [
            "📋 REGISTRO DE SERVICIO",
            "=" * 30,
            f"🕰️ Hora: {hora}",
            f"📅 Fecha: {fecha}",
            f"🕵️‍♂️ Turno: {turno}",
            f"👤 Usuario: {usuario}",
            "",
            "🚓 UNIDADES DISPONIBLES",
            "-" * 30
        ]

        # Unidades en formato vertical (una por línea)
        filtered_units = self._get_filtered_units()
        for unit in filtered_units:
            lines.append(f"🚓 {unit}")

        lines.extend([
            "",
            "👮 SIERRA BRAVOS",
            "-" * 30
        ])
        
        selected_sierra_bravos = [alias for alias, var in self.sierra_bravos_vars.items() if var.get()]
        if selected_sierra_bravos:
            for sb in selected_sierra_bravos:
                lines.append(f"🙎 {sb}")
        else:
            lines.append("Ninguno seleccionado")

        lines.extend([
            "",
            "🏍️ MOTORIZADOS",
            "-" * 30
        ])
        
        selected_motorizados = [alias for alias, var in self.motorizados_vars.items() if var.get()]
        if selected_motorizados:
            for mot in selected_motorizados:
                lines.append(f"🛵 {mot}")
        else:
            lines.append("Ninguno seleccionado")

        lines.extend([
            "",
            "🏢 BASES OPERATIVAS",
            "-" * 30
        ])
        
        selected_bases = [base for base, var in self.bases_vars.items() if var.get()]
        if selected_bases:
            for base in selected_bases:
                lines.append(f"🟩 {base}")
        else:
            lines.append("Ninguna seleccionada")

        lines.append("=" * 30)

        return "\n".join(lines)

    def _update_preview(self):
        report = self._build_report_text()
        self._mostrar_resultado(report)

    def _mostrar_resultado(self, texto: str):
        self.resultado_text.config(state='normal')
        self.resultado_text.delete("1.0", tk.END)
        self.resultado_text.insert(tk.END, texto)
        self.resultado_text.config(state='disabled')

    def _copy_report(self):
        text = self.resultado_text.get("1.0", tk.END).strip()
        if text:
            pyperclip.copy(text)
            ToastNotification(self.window, "✅ Registro copiado al portapapeles",
                              duration=3000, position='topright')

    def _clear_selection(self):
        """Limpia todas las selecciones."""
        for var in self.motorizados_vars.values():
            var.set(False)
        for var in self.sierra_bravos_vars.values():
            var.set(False)
        for var in self.bases_vars.values():
            var.set(False)
        self._update_preview()
        ToastNotification(self.window, "🗑️ Selección limpiada",
                          duration=2000, position='topright')

    def _on_close(self):
        DistribucionWindow._window_open = False
        self.window.destroy()

def abrir_ventana_distribucion(parent: tk.Tk, unidades_data: Dict[str, Any]):
    DistribucionWindow(parent, unidades_data)

if __name__ == "__main__":
    example_data = {
        'unidades_disponibles': [
            "T. NUEVA TALARA - P.7 DE JUNIO - AP. 28 DE JULIO - PQ.39",
            "H1 / EUI-621", "H2 / EUI-682", "H4 / EUI-684", "H5 / EUI-685",
            "H7 / EUI-687", "H9 / EUI-689", "H11 / EUI-691", "H12 / EUI-692",
            "H13 / EUI-693"
        ],
        'turno_actual': "DÍA",
        'filtro_activo': "TODAS",
        'alias_unidades': {},
        'camionetas': set(),
        'autos': set(),
        'unidades_manuales': []
    }
    root = tk.Tk()
    root.withdraw()
    abrir_ventana_distribucion(root, example_data)
    root.mainloop()