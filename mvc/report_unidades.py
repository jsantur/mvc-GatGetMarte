#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Optimizado: Reporte de Unidades
======================================
Aplicación para generar reportes de unidades con interfaz moderna y eficiente.

Autor: Sistema de Optimización
Fecha: 2025-06-12
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pyperclip
from datetime import datetime
import platform
import re
import os
import webbrowser
from PIL import Image, ImageTk, ImageDraw, ImageFont
from typing import Dict, List, Optional, Any
import json
from textwrap import wrap

# Importar utilidades centralizadas
from utils import UI_CONSTANTS, should_show_unit, ToastNotification, Validators, ModernEntry, get_base_path
import threading
from wialon_api import WialonAPI

from distribucion import abrir_ventana_distribucion

# Clase Principal
class ReportUnidadesWindowOptimized:
    _window_open = False

    def __init__(self, parent: tk.Tk, unidades_data: Dict[str, Any]):
        if ReportUnidadesWindowOptimized._window_open:
            ToastNotification(parent, "⚠️ Ya hay una ventana abierta.", duration=4000, position='center', style='warning', font_size=16, width=500)
            return
        self.parent = parent
        self.unidades_data = unidades_data
        self.unit_vars = {}
        self.obs_entries = {}
        self.entry_widgets = []
        self.obs_entries_list = []  # Lista para mantener el orden de las entradas de observación
        self._create_window()
        self._configure_styles()
        self._setup_bindings()
        ReportUnidadesWindowOptimized._window_open = True
        self._keep_on_top()

    def _create_window(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"{UI_CONSTANTS['ICONS']['report']} Reporte de Unidades - Optimizado")
        self.window.geometry(UI_CONSTANTS['WINDOW_SIZE'])
        self.window.resizable(False, False)
        self.window.configure(bg=UI_CONSTANTS['COLORS']['background'])
        self.window.protocol("WM_DELETE_WINDOW", lambda: None)  # Deshabilitar botón de cerrar
        self._create_header()
        self._create_main_content()
        self._create_status_bar()
        self.window.focus_force()

    def _create_header(self):
        header = tk.Frame(self.window, bg=UI_CONSTANTS['COLORS']['primary'], height=60)
        header.pack(fill=tk.X, pady=(0, 20))
        
        # Contenedor principal para imagen y textos
        content_frame = tk.Frame(header, bg=UI_CONSTANTS['COLORS']['primary'])
        content_frame.pack(expand=True, fill=tk.BOTH, padx=(60, 15), pady=(20, 5))
        
        # Cargar y mostrar la imagen
        try:
            image_path = os.path.join("help", "Unidades.png")
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
        title_label = tk.Label(text_frame, text="REPORTE DE UNIDADES", 
                              font=UI_CONSTANTS['FONTS']['title'], bg=UI_CONSTANTS['COLORS']['primary'], fg='white')
        title_label.pack(anchor=tk.W, pady=(0, 0))
        
        # Subtítulo con las instrucciones
        subtitle_label = tk.Label(text_frame, text="Auto-MAYÚSCULAS • Enter para avanzar entre campos • Copia rápida", 
                                 font=UI_CONSTANTS['FONTS']['small'], bg=UI_CONSTANTS['COLORS']['primary'], fg='#bdc3c7')
        subtitle_label.pack(anchor=tk.W, pady=(0, 0))
        
        # Instrucción para cerrar
        instruction_label = tk.Label(text_frame, text="💡 Presiona ESC para cerrar la ventana", 
                                    font=UI_CONSTANTS['FONTS']['small'], bg=UI_CONSTANTS['COLORS']['primary'], fg='#FFD700')
        instruction_label.pack(anchor=tk.W)
        
        # Botones para ubicación y monitoreo
        btn_frame = tk.Frame(header, bg=UI_CONSTANTS['COLORS']['primary'])
        btn_frame.pack(side=tk.RIGHT, padx=10)
        
        self.btn_ubicacion = ttk.Button(btn_frame, text="Ubicación 📍", command=self._consultar_ubicacion_wialon,
                style='Unidades.Secondary.TButton')
        self.btn_ubicacion.pack(side=tk.LEFT, padx=2)

    def _create_main_content(self):
        main = tk.Frame(self.window, bg=UI_CONSTANTS['COLORS']['background'])
        main.pack(fill=tk.BOTH, expand=True, padx=UI_CONSTANTS['PADDING']['large'])
        self.canvas = tk.Canvas(main, bg=UI_CONSTANTS['COLORS']['background'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=UI_CONSTANTS['COLORS']['background'])
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._create_time_section()
        self._create_units_section()
        self._create_action_section()
        self._create_output_section()

    def _create_time_section(self):
        time_frame = ttk.LabelFrame(self.scrollable_frame, text="⏰ Información Temporal", style='Modern.TLabelframe',
                                    padding=UI_CONSTANTS['PADDING']['medium'])
        time_frame.pack(fill=tk.X, pady=(0, UI_CONSTANTS['PADDING']['medium']))
        fields = tk.Frame(time_frame, bg=UI_CONSTANTS['COLORS']['card_bg'])
        fields.pack(fill=tk.X)
        tk.Label(fields, text=f"{UI_CONSTANTS['ICONS']['clock']} Hora:", font=UI_CONSTANTS['FONTS']['body'],
                 bg=UI_CONSTANTS['COLORS']['card_bg']).grid(row=0, column=0, sticky='w', padx=(0, 5))
        self.hora_entry = ModernEntry(fields, font=UI_CONSTANTS['FONTS']['body'], width=8, validator=Validators.validate_time)
        self.hora_entry.grid(row=0, column=1, padx=5)
        self.hora_entry.insert(0, datetime.now().strftime("%H:%M"))
        self.hora_entry.bind('<Return>', lambda e: self.obs_entries_list[0].focus_set() if self.obs_entries_list else None)
        self.entry_widgets.append(self.hora_entry)
        tk.Label(fields, text=f"{UI_CONSTANTS['ICONS']['calendar']} Fecha:", font=UI_CONSTANTS['FONTS']['body'],
                 bg=UI_CONSTANTS['COLORS']['card_bg']).grid(row=0, column=2, sticky='w', padx=(15, 5))
        self.fecha_entry = ModernEntry(fields, font=UI_CONSTANTS['FONTS']['body'], width=12, validator=Validators.validate_date)
        self.fecha_entry.grid(row=0, column=3, padx=5)
        self.fecha_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.fecha_entry.config(state='readonly')
        tk.Label(fields, text=f"{UI_CONSTANTS['ICONS']['users']} Turno:", font=UI_CONSTANTS['FONTS']['body'],
                 bg=UI_CONSTANTS['COLORS']['card_bg']).grid(row=0, column=4, sticky='w', padx=(15, 5))
        self.turno_label = tk.Label(fields, text=self.unidades_data.get('turno_actual', 'NOCHE'),
                                    font=UI_CONSTANTS['FONTS']['body'], bg=UI_CONSTANTS['COLORS']['card_bg'],
                                    fg=UI_CONSTANTS['COLORS']['primary'], width=8, anchor="w")
        self.turno_label.grid(row=0, column=5, padx=5)

    def _create_units_section(self):
        units_frame = ttk.LabelFrame(self.scrollable_frame, text=f"{UI_CONSTANTS['ICONS']['police']} Selección de Unidades",
                                     style='Modern.TLabelframe', padding=UI_CONSTANTS['PADDING']['medium'])
        units_frame.pack(fill=tk.BOTH, expand=True, pady=(0, UI_CONSTANTS['PADDING']['medium']))
        controls = tk.Frame(units_frame, bg=UI_CONSTANTS['COLORS']['card_bg'])
        controls.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(controls, text="✅ Seleccionar Todas", command=lambda: self._set_units(True), style='Unidades.Secondary.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls, text="❌ Deseleccionar Todas", command=lambda: self._set_units(False), style='Unidades.Secondary.TButton').pack(side=tk.LEFT)
        units_container = tk.Frame(units_frame, bg=UI_CONSTANTS['COLORS']['card_bg'])
        units_container.pack(fill=tk.BOTH, expand=True)
        self._create_units_list(units_container)

    def _create_units_list(self, parent):
        for alias in filter(self._should_show_unit, self.unidades_data.get('unidades_disponibles', [])):
            unit_frame = tk.Frame(parent, bg=UI_CONSTANTS['COLORS']['card_bg'])
            unit_frame.pack(fill=tk.X, pady=2)
            var = tk.BooleanVar(value=True)
            self.unit_vars[alias] = var
            tk.Checkbutton(unit_frame, variable=var, bg=UI_CONSTANTS['COLORS']['card_bg'], activebackground=UI_CONSTANTS['COLORS']['card_bg'],
                           command=lambda a=alias: self._toggle_obs(a)).pack(side=tk.LEFT, padx=5)
            tk.Label(unit_frame, text=alias, width=20, anchor="w", font=UI_CONSTANTS['FONTS']['body'],
                     bg=UI_CONSTANTS['COLORS']['card_bg'], fg=UI_CONSTANTS['COLORS']['text_primary']).pack(side=tk.LEFT)
            obs_entry = ModernEntry(unit_frame, width=50, font=UI_CONSTANTS['FONTS']['body'], uppercase=True, placeholder="Ingrese observación...")
            obs_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            self.obs_entries[alias] = obs_entry
            self.entry_widgets.append(obs_entry)
            self.obs_entries_list.append(obs_entry)
            idx = len(self.obs_entries_list) - 1
            obs_entry.bind('<Return>', lambda e, i=idx: self._focus_next_entry(i))

    def _focus_next_entry(self, current_idx):
        if not self.obs_entries_list:
            return
        next_idx = current_idx + 1
        if next_idx >= len(self.obs_entries_list):
            self.hora_entry.focus_set()
        else:
            self.obs_entries_list[next_idx].focus_set()

    def _should_show_unit(self, alias: str) -> bool:
        real_alias = self.unidades_data['alias_unidades'].get(alias, alias)
        filtro = self.unidades_data.get('filtro_activo', 'TODAS')
        return (filtro == "PICKUP" and real_alias in self.unidades_data.get('camionetas', set())) or \
               (filtro == "AUTOS" and real_alias in self.unidades_data.get('autos', set())) or \
               (filtro == "MANUAL" and alias in self.unidades_data.get('unidades_manuales', [])) or filtro == "TODAS"
        

    def _create_action_section(self):
        action_frame = tk.Frame(self.scrollable_frame, bg=UI_CONSTANTS['COLORS']['background'])
        action_frame.pack(fill=tk.X, pady=UI_CONSTANTS['PADDING']['medium'])
        ttk.Button(action_frame, text=f"{UI_CONSTANTS['ICONS']['copy']} Generar y Copiar Reporte", command=self._generar_reporte,
                   style='Unidades.Primary.TButton').pack(pady=5)
        secondary = tk.Frame(action_frame, bg=UI_CONSTANTS['COLORS']['background'])
        secondary.pack(fill=tk.X, pady=5)
        ttk.Button(secondary, text="🔄 Limpiar Todo", command=self._clear_all_fields, style='Unidades.Secondary.TButton', width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(secondary, text="📋 Vista Previa", command=self._preview_report, style='Unidades.Secondary.TButton', width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(secondary, text="🖨️ Imprimir", command=self._imprimir_reporte, style='Unidades.Secondary.TButton', width=15).pack(side=tk.LEFT, padx=5)

    def _create_output_section(self):
        output_frame = ttk.LabelFrame(self.scrollable_frame, text="📄 Reporte Generado", style='Modern.TLabelframe',
                                      padding=UI_CONSTANTS['PADDING']['medium'])
        output_frame.pack(fill=tk.BOTH, expand=True)
        self.resultado_text = tk.Text(output_frame, wrap=tk.WORD, height=12, font=UI_CONSTANTS['FONTS']['mono'], bg='#f8f9fa',
                                      fg=UI_CONSTANTS['COLORS']['text_primary'], padx=10, pady=10, state='disabled', relief="flat",
                                      borderwidth=1, highlightbackground=UI_CONSTANTS['COLORS']['border'], highlightthickness=1)
        self.resultado_text.pack(fill=tk.BOTH, expand=True)

    def _create_status_bar(self):
        self.status_bar = tk.Frame(self.window, bg=UI_CONSTANTS['COLORS']['primary'], height=25)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label = tk.Label(self.status_bar, text="Listo para generar reporte", bg=UI_CONSTANTS['COLORS']['primary'],
                                     fg='white', font=UI_CONSTANTS['FONTS']['small'])
        self.status_label.pack(side=tk.LEFT, padx=5)
        tk.Label(self.status_bar, text=f"🪪 Usuario: {platform.node().upper()}", bg=UI_CONSTANTS['COLORS']['primary'],
                 fg='white', font=UI_CONSTANTS['FONTS']['small']).pack(side=tk.RIGHT, padx=5)

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Modern.TLabelframe', background=UI_CONSTANTS['COLORS']['card_bg'], borderwidth=1, relief='solid')
        style.configure('Modern.TLabelframe.Label', background=UI_CONSTANTS['COLORS']['card_bg'], foreground=UI_CONSTANTS['COLORS']['text_primary'],
                        font=UI_CONSTANTS['FONTS']['subtitle'])
        # Estilos únicos para unidades para evitar conflictos
        style.configure('Unidades.Primary.TButton', font=UI_CONSTANTS['FONTS']['subtitle'], padding=(20, 10), foreground='white',
                        background=UI_CONSTANTS['COLORS']['secondary'])
        style.map('Unidades.Primary.TButton', background=[('active', '#2980b9'), ('pressed', '#21618c')])
        style.configure('Unidades.Secondary.TButton', font=UI_CONSTANTS['FONTS']['body'], padding=(10, 5), foreground=UI_CONSTANTS['COLORS']['text_primary'],
                        background=UI_CONSTANTS['COLORS']['background'])
        style.configure('Valid.TEntry', borderwidth=2, relief='solid', bordercolor=UI_CONSTANTS['COLORS']['valid'], foreground='black')
        style.configure('Invalid.TEntry', borderwidth=2, relief='solid', bordercolor=UI_CONSTANTS['COLORS']['error'], foreground='black')

    def _setup_bindings(self):
        self.window.bind('<Control-g>', lambda e: self._generar_reporte())
        self.window.bind('<Control-l>', lambda e: self._clear_all_fields())
        self.window.bind('<Control-p>', lambda e: self._preview_report())
        self.window.bind('<Control-a>', lambda e: self._set_units(True))
        self.window.bind('<Control-d>', lambda e: self._set_units(False))
        self.window.bind('<Control-c>', lambda e: self._copy_report())
        self.window.bind('<Escape>', lambda e: self._on_close())

    def _set_units(self, state: bool):
        for var, entry in zip(self.unit_vars.values(), self.obs_entries.values()):
            var.set(state)
            entry.config(state='normal' if state else 'disabled')
            if not state:
                entry.delete(0, tk.END)
        self._update_status(f"Todas las unidades {'seleccionadas' if state else 'deseleccionadas'}")

    def _clear_all_fields(self):
        for entry in self.obs_entries.values():
            if entry['state'] != 'disabled':
                entry.delete(0, tk.END)
        self.hora_entry.delete(0, tk.END)
        self.hora_entry.insert(0, datetime.now().strftime("%H:%M"))
        self._clear_output()
        self._update_status("Campos limpiados")

    def _clear_input_fields_only(self):
        """Limpia solo los campos de entrada, manteniendo el reporte visible"""
        for entry in self.obs_entries.values():
            if entry['state'] != 'disabled':
                entry.delete(0, tk.END)
        self.hora_entry.delete(0, tk.END)
        self.hora_entry.insert(0, datetime.now().strftime("%H:%M"))
        self._update_status("Campos de entrada limpiados, reporte mantenido")

    def _preview_report(self):
        # Validar campos antes de generar vista previa
        if not self._validate_fields():
            return
        
        report = self._build_report_text()
        if report:
            self._mostrar_resultado(report)
            self._update_status("Vista previa generada")
        else:
            ToastNotification(self.window, "❌ No se pudo generar la vista previa. Verifique los datos.", duration=3000, position='topright')
            self._update_status("Error al generar vista previa")

    def _toggle_obs(self, alias: str):
        entry = self.obs_entries[alias]
        state = 'normal' if self.unit_vars[alias].get() else 'disabled'
        entry.config(state=state)
        if state == 'disabled':
            entry.delete(0, tk.END)

    def _generar_reporte(self):
        # Validar campos antes de generar reporte
        if not self._validate_fields():
            return
        
        texto = self._build_report_text()
        if texto:
            pyperclip.copy(texto)
            self._mostrar_resultado(texto)
            self._guardar_reporte_json(texto)
            # Limpiar solo los campos de entrada, no el área de texto del reporte
            self._clear_input_fields_only()
            ToastNotification(self.window, "✅ Reporte copiado, guardado en JSON y campos listos para el siguiente reporte", duration=2000, position='topright')
            self._update_status("Reporte generado y copiado exitosamente")
        else:
            ToastNotification(self.window, "❌ No se pudo generar el reporte. Verifique los datos.", duration=3000, position='topright')
            self._update_status("Error al generar reporte")

    def _guardar_reporte_json(self, texto):
        fecha = datetime.now().strftime("%Y-%m-%d")
        hora = self.hora_entry.get().strip().replace(':', '-')  # Usar la hora ingresada por el usuario
        turno = self.turno_label.cget('text')
        # Limitar la cantidad de reportes por turno
        limites = {'DÍA': 5, 'TARDE': 5, 'NOCHE': 11}
        os.makedirs('reportes_json', exist_ok=True)
        file_path = os.path.join('reportes_json', f'reporte_{fecha}.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
        else:
            all_data = []
        # Evitar duplicados por hora y turno
        all_data = [r for r in all_data if not (r.get('hora') == hora and r.get('turno') == turno)]
        # Limitar la cantidad de reportes por turno
        reportes_turno = [r for r in all_data if r.get('turno') == turno]
        if len(reportes_turno) >= limites.get(turno, 5):
            ToastNotification(self.window, f"Ya se alcanzó el máximo de reportes para el turno {turno}", duration=2000, position='topright')
            return
        data = {
            'fecha': fecha,
            'hora': hora,
            'turno': turno,
            'reporte': texto
        }
        all_data.append(data)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

    def _imprimir_reporte(self):
        # Leer todos los reportes del día y turno actual
        fecha = datetime.now().strftime("%Y-%m-%d")
        turno = self.turno_label.cget('text')
        file_path = os.path.join('reportes_json', f'reporte_{fecha}.json')
        if not os.path.exists(file_path):
            ToastNotification(self.window, "No hay reportes almacenados para hoy", duration=2000, position='topright')
            return
        with open(file_path, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
        # Filtrar solo reportes del turno actual
        reportes_turno = [r for r in all_data if r.get('turno') == turno]
        if not reportes_turno:
            ToastNotification(self.window, f"No hay reportes para el turno {turno}", duration=2000, position='topright')
            return
        img_path = self._generar_imagen_tabla_reportes(reportes_turno, turno)
        if img_path:
            self._previsualizar_imagen(img_path)

    def _generar_imagen_tabla_reportes(self, reportes_turno, turno):
        # Evitar duplicados por hora
        seen_horas = set()
        bloques = []
        for rep in sorted(reportes_turno, key=lambda r: r.get('hora', '')):
            hora = rep.get('hora', '').replace('-', ':')
            if hora in seen_horas:
                continue
            seen_horas.add(hora)
            texto = rep.get('reporte', '')
            unidades = []
            lines = texto.split('\n')
            unidad_actual = None
            for line in lines:
                if line.startswith('🚓 '):
                    unidad_actual = {'unidad': line.replace('🚓 ', '').strip(), 'observacion': ''}
                elif line.strip().startswith('📝') and unidad_actual:
                    unidad_actual['observacion'] = line.replace('📝', '').strip()
                    unidades.append(unidad_actual)
                    unidad_actual = None
            bloques.append({'hora': hora, 'unidades': unidades})
        # Configuración de columnas
        num_columnas = 3
        num_filas = (len(bloques) + num_columnas - 1) // num_columnas
        col_width = 420
        unidad_col_width = 90  # Más compacto
        reporte_col_width = col_width - unidad_col_width - 30
        padding_obs = 50  # Espacio extra entre UNIDAD y REPORTE
        row_height_base = 28
        width = col_width * num_columnas + 80
        height = 120 + row_height_base * 8 * num_filas
        os.makedirs('img', exist_ok=True)
        img_path = os.path.join('img', f'reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png')
        image = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        try:
            font_title = ImageFont.truetype('arial.ttf', 28)
            font_header = ImageFont.truetype('arial.ttf', 22)
            font_table = ImageFont.truetype('arial.ttf', 13)  # Más pequeño para REPORTE
            font_bold = ImageFont.truetype('arialbd.ttf', 17)
        except:
            font_title = font_header = font_table = font_bold = ImageFont.load_default()
        # Encabezado grande
        encabezado = f'━━━━━━━━━🚓 REPORTE DE UNIDADES – TURNO {turno} ━━━━━━━━━'
        draw.text((width//2 - draw.textlength(encabezado, font=font_title)//2, 20), encabezado, fill=(0,56,147), font=font_title)
        y0 = 70
        # Dibujar cada bloque en su columna/fila
        for idx, bloque in enumerate(bloques):
            col = idx % num_columnas
            fila = idx // num_columnas
            x = 40 + col * col_width
            y = y0 + fila * row_height_base * 8
            # Encabezado de bloque
            draw.rectangle([(x, y), (x+col_width-20, y+30)], fill=(0,56,147))
            draw.text((x+10, y+5), f'UNIDAD', fill='white', font=font_header)
            draw.text((x+col_width//2, y+5), f'REPORTE: {bloque["hora"]}', fill='white', font=font_header)
            y += 30
            # Dibujar filas de unidades
            for unidad in bloque['unidades']:
                obs = unidad['observacion']
                max_line_length = 38
                wrapped_obs = wrap(obs, width=max_line_length)
                cell_height = row_height_base * max(1, len(wrapped_obs))
                draw.rectangle([(x, y), (x+col_width-20, y+cell_height)], fill=(255,255,255))
                draw.text((x+10, y+5), unidad['unidad'], fill=(0,0,0), font=font_bold)
                for i, line in enumerate(wrapped_obs):
                    draw.text((x+unidad_col_width+padding_obs, y+5 + i*row_height_base), line, fill=(0,0,0), font=font_table)
                y += cell_height
            # Borde alrededor del bloque
            draw.rectangle([(x, y0 + fila * row_height_base * 8), (x+col_width-20, y-1)], outline=(0,56,147), width=2)
        image.save(img_path)
        return img_path

    def _previsualizar_imagen(self, img_path):
        preview = tk.Toplevel(self.window)
        preview.title('Vista Previa del Reporte')
        img = Image.open(img_path)
        img.thumbnail((800, 1000))
        tk_img = ImageTk.PhotoImage(img)
        label = tk.Label(preview, image=tk_img)
        label.pack()
        self.preview_img = tk_img  # Mantener referencia para evitar garbage collection
        ttk.Button(preview, text='Imprimir', command=lambda: self._imprimir_archivo(img_path)).pack(pady=10)

    def _imprimir_archivo(self, img_path):
        # Abrir diálogo de impresión del sistema
        os.startfile(img_path, 'print')

    def _validate_fields(self) -> bool:
        hora = self.hora_entry.get().strip()
        if not hora or not Validators.validate_time(hora):
            ToastNotification(self.window, "⏰ La hora debe ser en formato HH:MM.", duration=3000, position='topright')
            self.hora_entry.focus_set()
            return False
        selected = [(alias, self.obs_entries[alias].get().strip()) for alias, var in self.unit_vars.items() if var.get()]
        if not selected:
            ToastNotification(self.window, "📝 Seleccione al menos una unidad.", duration=3000, position='topright')
            return False
        empty = [alias for alias, obs in selected if not obs or obs == "Ingrese observación..."]
        if empty:
            unit_list = "\n".join([f"• {unit}" for unit in empty[:5]]) + (f"\n... y {len(empty) - 5} más" if len(empty) > 5 else "")
            ToastNotification(self.window, f"📝 Unidades sin observaciones:\n\n{unit_list}", duration=3000, position='topright')
            self.obs_entries[empty[0]].focus_set()
            return False
        return True

    def _build_report_text(self) -> Optional[str]:
        try:
            # Diseño optimizado para móvil - formato vertical y compacto
            lines = [
                "📋 REPORTE DE UNIDADES",
                "=" * 30,
                f"🕰️ Hora: {self.hora_entry.get().strip()}",
                f"📅 Fecha: {self.fecha_entry.get().strip()}",
                f"🕵️‍♂️ Turno: {self.turno_label.cget('text')}",
                "",
                "🚓 UNIDADES SELECCIONADAS",
                "-" * 30
            ]
            
            selected_count = 0
            for alias, var in self.unit_vars.items():
                if var.get():
                    observation = Validators.sanitize_observation(self.obs_entries[alias].get())
                    lines.append(f"🚓 {alias}")
                    lines.append(f"   📝 {observation}")
                    lines.append("")  # Línea en blanco para separar
                    selected_count += 1
            
            if not selected_count:
                return None
                
            lines.extend([
                "=" * 30,
                f"👤 Usuario: {platform.node().upper()}"
            ])
            
            return "\n".join(lines)
        except Exception as e:
            ToastNotification(self.window, f"Error al construir reporte: {str(e)}", duration=3000, position='topright')
            return None

    def _clear_observation_fields(self):
        for alias, var in self.unit_vars.items():
            if var.get():
                self.obs_entries[alias].delete(0, tk.END)

    def _mostrar_resultado(self, texto: str):
        self.resultado_text.config(state='normal')
        self.resultado_text.delete("1.0", tk.END)
        self.resultado_text.insert(tk.END, texto)
        self.resultado_text.config(state='disabled')

    def _clear_output(self):
        self.resultado_text.config(state='normal')
        self.resultado_text.delete("1.0", tk.END)
        self.resultado_text.config(state='disabled')

    def _copy_report(self):
        text = self.resultado_text.get("1.0", tk.END).strip()
        if text:
            pyperclip.copy(text)
            ToastNotification(self.window, "Reporte copiado al portapapeles", duration=3000, position='topright')
            self._update_status("Reporte copiado al portapapeles")

    def _update_status(self, message: str):
        if self.status_label.winfo_exists():
            self.status_label.config(text=message)
            self.window.after(5000, lambda: self.status_label.config(text="Listo para generar reporte") if self.status_label.winfo_exists() else None)

    def _keep_on_top(self):
        self.window.attributes('-topmost', True)
        self.window.after(1000, self._check_topmost)

    def _check_topmost(self):
        try:
            if self.window.winfo_exists() and not self.window.attributes('-topmost'):
                self.window.attributes('-topmost', True)
            self.window.after(1000, self._check_topmost)
        except tk.TclError:
            pass

    def _on_close(self):
        ReportUnidadesWindowOptimized._window_open = False
        self.window.destroy()

    def _consultar_ubicacion_wialon(self):
        """Consulta la ubicación actual de las unidades en Wialon (forzando actualización).
        Muestra solo estado y dirección. Indicador sutil si datos tienen >5 minutos de retraso."""
        def ejecutar_consulta():
            try:
                self._update_status("📡 Consultando ubicación actual en Wialon...")
                
                # Cargar configuración del token
                from utils import get_base_path
                config_path = os.path.join(get_base_path(), "config.json")
                if not os.path.exists(config_path):
                    self.window.after(0, lambda: ToastNotification(self.window, "❌ Error: config.json no encontrado", style='error'))
                    return
                
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                token = config.get("wialon_config", {}).get("token")
                if not token:
                    self.window.after(0, lambda: ToastNotification(self.window, "❌ Error: Token no configurado", style='error'))
                    return

                # Mapeo de unidades para Wialon (solo las que nos interesan, pero podemos consultar todas y filtrar después)
                mapping_wialon = {
                    "H1": "1  EUI-621", "H2": "2  EUI-682", "H3": "3  EUI-683",
                    "H4": "4  EUI-646", "H5": "5  EUI-685", "H6": "6  EUI-686",
                    "H7": "7  EUI-679", "H8": "8  EUI-680", "H9": "9  EUI-645",
                    "H10": "10  EUI-647", "H11": "11  EUI-668", "H12": "12  EUI-670",
                    "H13": "13  EUI-671"
                }
                
                api = WialonAPI(token)
                # Obtener datos DETALLADOS (incluye full_address, lat, lon)
                detailed_data = api.get_units_realtime_status(list(mapping_wialon.values()), detailed=True)
                api.logout()
                
                if not detailed_data:
                    self.window.after(0, lambda: ToastNotification(self.window, "⚠️ No se encontraron unidades activas en Wialon", style='warning'))
                    self._update_status("⚠️ Wialon: Sin unidades encontradas")
                    return

                # Obtener lista de alias de UI que están actualmente visibles (según filtro)
                visible_aliases = [alias for alias in self.unit_vars.keys() if self._should_show_unit(alias)]
                
                # Crear mapeo inverso: código de placa -> nombre Wialon
                # mapping_wialon = {"H1": "1  EUI-621", ...} -> codigo_placa -> "1  EUI-621"
                codigo_a_wialon = {}
                for wialon_alias, wialon_name in mapping_wialon.items():
                    # Extraer la placa del nombre Wialon (ej: "EUI-621" de "1  EUI-621")
                    match = re.search(r'(EUI-\d+)', wialon_name)
                    if match:
                        placa = match.group(1)
                        codigo_a_wialon[placa] = wialon_name
                
                actualizadas = 0
                # Recorrer las entradas de observación de la UI
                for alias_ui, entry in self.obs_entries.items():
                    # Verificar si esta unidad está visible en la lista actual
                    if alias_ui not in visible_aliases:
                        continue
                    
                    # Obtener el código real de la unidad desde alias_unidades
                    # alias_ui = "🚙 1 EUI-621" -> codigo_real = "EUI-621"
                    codigo_real = self.unidades_data.get('alias_unidades', {}).get(alias_ui)
                    if not codigo_real:
                        # Fallback: intentar extraer directamente del alias con regex más robusto
                        match = re.search(r'(EUI-\d+)', alias_ui)
                        if match:
                            codigo_real = match.group(1)
                    
                    if not codigo_real:
                        continue
                    
                    # Buscar el nombre Wialon correspondiente al código
                    unit_num = codigo_a_wialon.get(codigo_real)
                    if not unit_num:
                        continue
                    
                    if unit_num in detailed_data:
                        info = detailed_data[unit_num]
                        status = info.get("status", "?")
                        full_addr = info.get("full_address", info.get("address", "Ubicación desconocida"))
                        es_reciente = info.get("es_reciente", False)
                        antiguedad = info.get("antiguedad_min", 0)
                        
                        # Mostrar solo estado y dirección (sin hora)
                        if es_reciente:
                            ubicacion_texto = f"{status}. {full_addr}"
                        else:
                            # Indicador sutil de antigüedad sin mostrar la hora exacta
                            ubicacion_texto = f"{status}. {full_addr} (⚠️ datos con {antiguedad:.0f}min de retraso)"
                        
                        self.window.after(0, lambda e=entry, v=ubicacion_texto: self._update_entry_value(e, v))
                        actualizadas += 1
                
                if actualizadas > 0:
                    self._update_status(f"✅ Ubicación cargada en {actualizadas} unidades")
                    self.window.after(0, lambda: ToastNotification(self.window, f"✅ {actualizadas} ubicaciones actualizadas", duration=3000))
                else:
                    self.window.after(0, lambda: ToastNotification(self.window, "⚠️ No se pudieron emparejar las unidades visibles", style='warning'))
                    self._update_status("⚠️ Error de emparejamiento")
                
            except Exception as e:
                self.window.after(0, lambda: ToastNotification(self.window, f"❌ Error: {str(e)}", style='error'))
                self._update_status("❌ Error en consulta Wialon")

        threading.Thread(target=ejecutar_consulta, daemon=True).start()

    def _update_entry_value(self, entry, value):
        """Actualiza el valor de una entrada de texto y activa la validación."""
        entry.delete(0, tk.END)
        entry.configure(foreground='black')  # Forzar color negro antes de insertar
        entry.insert(0, value)
        entry.event_generate('<KeyRelease>')

def abrir_ventana_unidades(parent: tk.Tk, unidades_data: Dict[str, Any]):

    ReportUnidadesWindowOptimized(parent, unidades_data)

def main():
    example_data = {
        'unidades_disponibles': [
            "T. NUEVA TALARA - P.7 DE JUNIO - AP. 28 DE JULIO - PQ.39",
            "H1 / EUI-621", "H2 / EUI-682", "H3 / EUI-683", "PICKUP-01", "AUTO-PATRULLA-01"
        ],
        'alias_unidades': {
            "H1 / EUI-621": "EUI-621", "H2 / EUI-682": "EUI-682", "H3 / EUI-683": "EUI-683"
        },
        'camionetas': {"EUI-621", "EUI-682", "EUI-683", "PICKUP-01"},
        'autos': {"AUTO-PATRULLA-01"},
        'turno_actual': "NOCHE",
        'filtro_activo': "TODAS",
        'unidades_manuales': []
    }
    root = tk.Tk()
    root.withdraw()
    abrir_ventana_unidades(root, example_data)
    root.mainloop()

if __name__ == "__main__":
    main()