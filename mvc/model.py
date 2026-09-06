# model.py (versión ULTRA-OPTIMIZADA con validación robusta) - CORREGIDO
import hashlib
import locale
import base64
import io
import math
import time
import tkinter as tk
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
import os
import sqlite3
import json
from pathlib import Path
import pickle
import sys
from datetime import datetime, timedelta
import threading
import shutil
from typing import Dict, List, Tuple, Optional, Any
from cache import OptimizedCacheManager, CacheConfig
import glob
import requests
import certifi      # IMPORTANTE para certificados SSL en modo EXE
import logging
logger = logging.getLogger(__name__)

# Reemplazar pandas si es posible
try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    mysql = None
    print("Advertencia: mysql-connector no disponible")

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None
    print("Advertencia: Pillow no disponible para generación de reportes")

# Importar módulos centralizados
from utils import get_base_path, resource_path, resource_manager
from units_manager import units_manager

class OptimizedModel:
    """Modelo optimizado con gestión robusta de datos y caché avanzado."""
    
    def __init__(self, cache_manager=None):
        # CORRECCIÓN: Inicializar el lock primero
        self._data_lock = threading.Lock()
        
        # Configuración de caché optimizada
        cache_config = CacheConfig(
            max_memory_size=2000,
            max_memory_mb=300,
            max_disk_mb=1000,
            compression_threshold=1024,
            cleanup_interval=600,
            max_threads=4
        )
        self.cache = cache_manager or OptimizedCacheManager("model_cache", cache_config)
        
        # Cargar configuración desde caché o inicializar
        self._load_or_initialize_config()

        # Usar el gestor centralizado de unidades
        self._cargar_unidades_desde_archivo()
                        
        self.IMG_FOLDER = "IMG"
        self.LINK_WIALON = "https://hosting.wialon.us/?lang=es"
        self.LINK_SIPCOP = "https://seguridadciudadana.mininter.gob.pe/sipcop-m/reportes/mapa-recorrido-vehiculo"
        
        # Configurar locale para fechas
        self._setup_locale()

        # Configurar archivo de respaldo Excel
        self.EXCEL_BACKUP_FILE = os.path.join(get_base_path(), "unidades_registro.xlsx")
        self._initialize_excel_backup()
        
        # Cargar URL de la nube y configuración de Wialon desde config.json
        config = self._load_full_config()
        self.CLOUD_API_URL = config.get("cloud_api_url", "")
        self.WIALON_CONFIG = config.get("wialon_config", {})
        
        # Mapeo de unidades para Wialon (corregido con doble espacio como aparece en API)
        self.WIALON_MAPPING = {
            "H1": "1  EUI-621", "H2": "2  EUI-682", "H3": "3  EUI-683",
            "H4": "4  EUI-646", "H5": "5  EUI-685", "H6": "6  EUI-686",
            "H7": "7  EUI-679", "H8": "8  EUI-680", "H9": "9  EUI-645",
            "H10": "10  EUI-647", "H11": "11  EUI-668", "H12": "12  EUI-670",
            "H13": "13  EUI-671"
        }
        
        # Inicializar SQLite
        self.DB_PATH = os.path.join(get_base_path(), "serenazgo_db.sqlite")
        self._initialize_sqlite()
        
        # Intentar migración si es necesario
        threading.Thread(target=self._migrate_excel_to_sqlite, daemon=True).start()

    def _load_full_config(self) -> dict:
        """Carga toda la configuración desde config.json."""
        try:
            external_path = os.path.join(get_base_path(), "config.json")
            internal_path = resource_path("config.json")
            config_path = external_path if os.path.exists(external_path) else internal_path
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error al cargar config.json: {e}")
            return {}
            logger.error(f"❌ Error cargando URL de nube: {e}")
            return ""

    
    def _setup_locale(self):
        """Configura el locale del sistema para fechas."""
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Linux
        except locale.Error:
            try:
                locale.setlocale(locale.LC_TIME, 'spanish')  # Windows
            except locale.Error:
                print("[ADVERTENCIA] No se pudo configurar locale español")

    def _cargar_unidades_desde_archivo(self):
        """Carga las unidades usando el gestor centralizado."""
        try:
            with self._data_lock:
                # Usar el gestor centralizado de unidades
                units_data = units_manager.get_all_data()
                
                self.ALIAS_UNIDADES = units_data['alias_unidades']
                self.CAMIONETAS = units_data['camionetas']
                self.AUTOS = units_data['autos']
                self.UNIDADES_DISPONIBLES = units_data['unidades_disponibles']
                
                # Guardar en caché para acceso rápido
                self.cache.set("units_data", units_data, persist=True)
                
                print(f"[MODELO] Unidades cargadas desde gestor centralizado: {len(self.UNIDADES_DISPONIBLES)} unidades")
                
        except Exception as e:
            print(f"[ERROR] Error crítico cargando unidades: {e}")
            raise

    def _load_or_initialize_config(self):
        """Carga configuración desde caché o inicializa valores por defecto."""
        try:
            config = self.cache.get("model_config")
            if config:
                # Aplicar configuración cargada
                for key, value in config.items():
                    setattr(self, key, value)
                print("[MODELO] Configuración cargada desde caché")
            else:
                # Inicializar configuración por defecto
                self._initialize_default_config()
                
        except Exception as e:
            print(f"[ERROR] Error cargando configuración: {e}")
            self._initialize_default_config()
    
    def _initialize_default_config(self):
        """Inicializa configuración por defecto."""
        default_config = {
            'version': '2.0',
            'last_update': datetime.now().isoformat(),
            'validation_rules': {
                'km_min': 0,
                'km_max': 999999,
                'ap_min': 0,
                'ap_max': 999999,
                'po_min': 0,
                'po_max': 10
            }
        }
        
        # Aplicar y guardar configuración
        for key, value in default_config.items():
            setattr(self, key, value)
        
        self.cache.set("model_config", default_config, persist=True)
        print("[MODELO] Configuración por defecto inicializada")

    def _initialize_excel_backup(self):
        """Inicializa el archivo de respaldo Excel si no existe."""
        try:
            if not os.path.exists(self.EXCEL_BACKUP_FILE):
                # Crear un libro de trabajo básico
                import openpyxl
                workbook = openpyxl.Workbook()
                worksheet = workbook.active
                worksheet.title = "Registro de Unidades"
                
                # Encabezados exactos solicitados
                headers = ['FECHA', 'HORA', 'UNIDAD', 'KM', 'AP', 'PO', 'TURNO', 'JURISDICCION', 'ZONA', 'OBSERVACIONES']
                for col, header in enumerate(headers, 1):
                    worksheet.cell(row=1, column=col, value=header)
                
                # Aplicar estilo a encabezados
                header_font = Font(bold=True, color="FFFFFF")
                header_fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
                
                for col in range(1, len(headers) + 1):
                    cell = worksheet.cell(row=1, column=col)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal="center")
                
                workbook.save(self.EXCEL_BACKUP_FILE)
                print(f"[MODELO] Archivo Excel inicializado (BDMarte format): {self.EXCEL_BACKUP_FILE}")

                
        except Exception as e:
            print(f"[ERROR] Error inicializando archivo Excel: {e}")

    def _initialize_sqlite(self):
        """Inicializa la base de datos SQLite y crea la tabla si no existe."""
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS registros (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha TEXT,
                        hora TEXT,
                        unidad TEXT,
                        km TEXT,
                        ap TEXT,
                        po TEXT,
                        turno TEXT,
                        jurisdiccion TEXT,
                        zona TEXT,
                        observaciones TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                # Add migration for existing DB
                try:
                    cursor.execute('ALTER TABLE registros ADD COLUMN zona TEXT')
                except sqlite3.OperationalError:
                    pass # Column might already exist
                conn.commit()
            print(f"[MODELO] Base de datos SQLite inicializada: {self.DB_PATH}")
        except Exception as e:
            print(f"[ERROR] Error inicializando SQLite: {e}")

    def _migrate_excel_to_sqlite(self):
        """Migra datos desde Excel a SQLite si SQLite está vacío."""
        try:
            # Verificar si SQLite tiene datos
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM registros")
                count = cursor.fetchone()[0]
            
            if count > 0:
                # Ya hay datos, no migrar
                return

            if not os.path.exists(self.EXCEL_BACKUP_FILE):
                return

            print(f"[MODELO] Iniciando migración automática de Excel a SQLite...")
            df = pd.read_excel(self.EXCEL_BACKUP_FILE, engine='openpyxl')
            if df.empty:
                return

            # Normalizar columnas (soportar formatos antiguos y nuevos)
            map_cols = {
                'FECHA': 'FECHA', 'HORA': 'HORA', 'UNIDAD': 'UNIDAD', 
                'KM': 'KM', 'AP': 'AP', 'PO': 'PO', 'TURNO': 'TURNO', 
                'JURISDICCION': 'JURISDICCION', 'OBSERVACIONES': 'OBSERVACIONES'
            }
            if 'FECHA' not in df.columns:
                 map_cols = {
                    '📅 FECHA': 'FECHA', '🕰️ HORA': 'HORA', '🚓 UNIDADES': 'UNIDAD',
                    '🚔 KM': 'KM', '📌 A.P': 'AP', '📒 P.O': 'PO', '🕵️‍♂️ TURNO': 'TURNO',
                    '🌙 OBS-TURNO': 'JURISDICCION', '✍ OBSERVACIONES ⛑': 'OBSERVACIONES'
                }

            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                for _, row in df.iterrows():
                    try:
                        cursor.execute('''
                            INSERT INTO registros (fecha, hora, unidad, km, ap, po, turno, jurisdiccion, zona, observaciones)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            str(row.get(map_cols.get('FECHA'), '')),
                            str(row.get(map_cols.get('HORA'), '')),
                            str(row.get(map_cols.get('UNIDAD', 'UNIDAD'))),
                            str(row.get(map_cols.get('KM', 'KM'))),
                            str(row.get(map_cols.get('AP', 'AP'))),
                            str(row.get(map_cols.get('PO', 'PO'))),
                            str(row.get(map_cols.get('TURNO', 'TURNO'))),
                            str(row.get(map_cols.get('JURISDICCION', 'JURISDICCION'))),
                            str(row.get('ZONA', '')),
                            str(row.get(map_cols.get('OBSERVACIONES', 'OBSERVACIONES')))
                        ))
                    except Exception as row_error:
                        print(f"Error migrando fila: {row_error}")
                conn.commit()
            
            print(f"[MODELO] Migración de Excel a SQLite completada: {len(df)} registros importados.")

        except Exception as e:
            print(f"[ERROR] Error durante la migración: {e}")

    def get_unit_info(self) -> Tuple[List[str], Dict[str, str], set, set]:
        """Obtiene información de unidades actualizada directamente del gestor."""
        # Eliminar cualquier caché obsoleto si existiera
        self.cache.delete("unit_info_complete")
        with self._data_lock:
            return (
                self.UNIDADES_DISPONIBLES[:],
                self.ALIAS_UNIDADES.copy(),
                self.CAMIONETAS.copy(),
                self.AUTOS.copy()
            )

    def calcular_observaciones(self, km: str, ap: str, po: str) -> Tuple[Tuple[str, str], Tuple[str, str], Tuple[str, str]]:
        """Calcula observaciones con validación optimizada y caché."""
        # Crear clave de caché
        cache_key = f"obs_{km}_{ap}_{po}"
        cached_result = self.cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Calcular observaciones
        obs_km = self._validar_km(km)
        obs_ap = self._validar_ap(ap)
        obs_po = self._validar_po(po)
        
        result = (obs_km, obs_ap, obs_po)
        
        # Guardar en caché por corto tiempo
        self.cache.set(cache_key, result, persist=False)
        
        return result
    
    def _validar_km(self, km: str) -> Tuple[str, str]:
        """Valida campo KM según nuevos requisitos."""
        if not km or not km.strip():
            return ("⚠️ 90 KM requerido", "#E6CEA1")
        
        try:
            km_int = int(km)
            if km_int < 0:
                return ("❌ KM no puede ser negativo", "red")
            
            objetivo_km = 90
            if km_int >= objetivo_km:
                # Solo mostrar excedente si supera los 100 KM
                if km_int > 100:
                    excedente = km_int - 100
                    return (f"✅ COMPLETO (+{excedente} KM)", "green")
                return ("✅ COMPLETO", "green")
            else:
                faltante = objetivo_km - km_int
                return (f"❌ FALTA {faltante} KM", "red")
                
        except ValueError:
            return ("❌ KM debe ser numérico", "red")

    def _validar_ap(self, ap: str) -> Tuple[str, str]:
        """Valida campo Auxilio Público según nuevos requisitos."""
        if not ap or not ap.strip():
            return ("⚠️ 230 AP requerido", "#E6CEA1")
        
        try:
            ap_int = int(ap)
            if ap_int < 0:
                return ("❌ AP no puede ser negativo", "red")
            
            objetivo_min = 230
            minutos_por_tactico = 30
            
            if ap_int >= objetivo_min:
                return ("✅ COMPLETO", "green")
            else:
                faltante_min = objetivo_min - ap_int
                faltante_tacticos = math.ceil(faltante_min / minutos_por_tactico)
                return (f"❌ FALTA {faltante_min} MIN ({faltante_tacticos}T)", "red")
                
        except ValueError:
            return ("❌ AP debe ser numérico", "red")

    def _validar_po(self, po: str) -> Tuple[str, str]:
        """Valida campo Parte de Ocurrencias según nuevos requisitos."""
        if not po or not po.strip():
            return ("⚠️ PO requerido", "#E6CEA1")
        
        try:
            po_int = int(po)
            if po_int < 0:
                return ("❌ PO no puede ser negativo", "red")
            
            minimo_requerido = 3
            maximo_permitido = 10
            
            if po_int > maximo_permitido:
                return (f"❌ PO máximo {maximo_permitido}", "red")
            elif po_int >= minimo_requerido:
                return (f"✅ COMPLETO ({po_int} P.O.)", "green")
            else:
                faltante = minimo_requerido - po_int
                return (f"❌ FALTAN {faltante} P.O.", "red")
                
        except ValueError:
            return ("❌ PO debe ser numérico", "red")
                
    def _get_observaciones_concatenadas(self, km: str, ap: str, po: str) -> str:
        """Genera una cadena de observaciones sin emojis para persistencia."""
        obs_km = self._validar_km(km)[0]
        obs_ap = self._validar_ap(ap)[0]
        obs_po = self._validar_po(po)[0]
        
        # Función auxiliar para limpiar emojis y avisos
        def limpiar(texto):
            for emoji in ["✅", "❌", "⚠️", "🤔"]:
                texto = texto.replace(emoji, "")
            return texto.strip()
        
        return f"{limpiar(obs_km)}, {limpiar(obs_ap)}, {limpiar(obs_po)}"

    def guardar_registro(self, units_data: List[Dict], turno: str, filtro_activo: str = "TODAS") -> bool:

        """Guarda registro con validación."""
        try:
            with self._data_lock:
                # Obtener marcas de tiempo actuales
                now = datetime.now()
                fecha = now.strftime('%d/%m/%Y')
                hora = now.strftime('%H:%M:%S')

                # Pre-calcular observaciones limpias (sin emojis) para cada unidad
                for unit in units_data:
                    unit['observaciones'] = self._get_observaciones_concatenadas(unit['km'], unit['ap'], unit['po'])

                # Guardar en múltiples formatos para redundancia
                success_json = self._save_to_json(units_data, turno, filtro_activo)
                success_sqlite = self._save_to_sqlite(units_data, turno, fecha, hora)
                success_excel = self._save_to_excel(units_data, turno, fecha, hora)
                
                # Intentar guardado en la nube (Google Sheets)
                success_cloud = self._save_to_cloud(units_data, turno, fecha, hora)
                
                success_cache = self._save_to_cache(units_data, turno, filtro_activo)
                
                # Consideramos éxito si al menos un formato persistente funciona
                if success_sqlite or success_excel or success_cloud:
                    self._update_last_save_info(units_data, turno)
                    cloud_msg = " (Sincronizado con BDMarte)" if success_cloud else " (Solo Local - Sin Nube)"
                    print(f"[MODELO] Registro guardado exitosamente{cloud_msg}")
                    return True
                else:
                    print(f"[ERROR] Falló guardado en todos los formatos persistentes")
                    return False


                    
        except Exception as e:
            print(f"[ERROR] Error guardando registro: {e}")
            return False
    
    def _validate_units_data(self, units_data: List[Dict]) -> bool:
        """Valida los datos de unidades antes de guardar."""
        if not units_data:
            print("[ERROR] No hay datos para guardar")
            return False
        
        for unit in units_data:
            required_fields = ['alias', 'km', 'ap', 'po']
            if not all(field in unit for field in required_fields):
                print(f"[ERROR] Datos incompletos para unidad: {unit}")
                return False
        
        return True

    def _normalize_unit_data(self, unit_raw: dict) -> dict:
        """Convierte cualquier diccionario de unidad a un formato estándar."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Manejo de alias
        alias = unit_raw.get('alias', unit_raw.get('unidad', ''))
        if not alias or str(alias).lower() == 'nan' or str(alias) == 'None':
            alias = ''
        
        # Conversión segura a string, limpiando valores nan/None
        def clean_value(val):
            if val is None:
                return ''
            val_str = str(val).strip()
            if val_str.lower() == 'nan' or val_str == 'None':
                return ''
            return val_str
        
        km = clean_value(unit_raw.get('km', ''))
        ap = clean_value(unit_raw.get('ap', ''))
        po = clean_value(unit_raw.get('po', ''))
        
        # Turnos seleccionados: puede ser lista o string separado por comas
        turnos_raw = unit_raw.get('turnos_seleccionados', [])
        if isinstance(turnos_raw, str):
            turnos = [t.strip() for t in turnos_raw.split(',') if t.strip() and t.strip().lower() != 'nan']
        elif isinstance(turnos_raw, list):
            turnos = [t for t in turnos_raw if t and str(t).lower() != 'nan']
        else:
            turnos = []
        
        # Jurisdicción
        jurisdiccion = clean_value(unit_raw.get('jurisdiccion', 'SECTORIAL'))
        if not jurisdiccion:
            jurisdiccion = 'SECTORIAL'
        
        return {
            'alias': alias,
            'km': km,
            'ap': ap,
            'po': po,
            'turnos_seleccionados': turnos,
            'jurisdiccion': jurisdiccion
        }
    
    def _save_to_json(self, units_data: List[Dict], turno: str, filtro_activo: str = "TODAS") -> bool:
        """Guarda datos en formato JSON."""
        try:
            json_dir = "data_json"
            os.makedirs(json_dir, exist_ok=True)
            
            timestamp = datetime.now()
            filename = f"registro_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(json_dir, filename)
            
            data_to_save = {
                'timestamp': timestamp.isoformat(),
                'turno': turno,
                'units': units_data,
                'filtro_activo': filtro_activo,
                'metadata': {
                    'version': getattr(self, 'version', '2.0'),
                    'total_units': len(units_data)
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
            
            print(f"[MODELO] Guardado JSON: {filepath}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error guardando JSON: {e}")
            return False
    
    def _save_to_excel(self, units_data: List[Dict], turno: str, fecha: str, hora: str) -> bool:
        """Guarda datos en archivo Excel con la nueva estructura BDMarte."""
        try:
            print(f"[DEBUG] Guardando en Excel local: {self.EXCEL_BACKUP_FILE}")
            import openpyxl
            
            # Crear respaldo automático antes de guardar
            self._create_excel_backup()
            
            # Cargar o crear libro de trabajo
            if os.path.exists(self.EXCEL_BACKUP_FILE):
                workbook = openpyxl.load_workbook(self.EXCEL_BACKUP_FILE)
                worksheet = workbook.active
            else:
                self._initialize_excel_backup()
                workbook = openpyxl.load_workbook(self.EXCEL_BACKUP_FILE)
                worksheet = workbook.active
            
            # Sincronizar encabezados si el archivo es antiguo
            if worksheet.cell(row=1, column=1).value != "FECHA":
                self._initialize_excel_backup()
                workbook = openpyxl.load_workbook(self.EXCEL_BACKUP_FILE)
                worksheet = workbook.active

            # Encontrar la siguiente fila disponible
            next_row = worksheet.max_row + 1
            
            # Agregar datos por cada unidad
            for unit in units_data:
                # Usar la observación pre-calculada
                observaciones_final = unit.get('observaciones', "COMPLETO, COMPLETO, COMPLETO")
                
                # Mapeo según solicitud del usuario:
                # Column G (7): TURNO (Checkboxes: NOCHE, DÍA)
                # Column H (8): JURISDICCION (Combobox: SECTORIAL, T.ALTA)
                # Column I (9): OBSERVACIONES (Concatenado)
                
                worksheet.cell(row=next_row, column=1, value=fecha)
                worksheet.cell(row=next_row, column=2, value=hora)
                worksheet.cell(row=next_row, column=3, value=unit['alias'])
                worksheet.cell(row=next_row, column=4, value=unit['km'])
                worksheet.cell(row=next_row, column=5, value=unit['ap'])
                worksheet.cell(row=next_row, column=6, value=unit['po'])
                worksheet.cell(row=next_row, column=7, value=', '.join(unit.get('turnos_seleccionados', [])))
                worksheet.cell(row=next_row, column=8, value=unit.get('jurisdiccion', 'SECTORIAL'))
                worksheet.cell(row=next_row, column=9, value=unit.get('zona', ''))
                worksheet.cell(row=next_row, column=10, value=observaciones_final)
                
                next_row += 1

            
            workbook.save(self.EXCEL_BACKUP_FILE)
            print(f"[MODELO] Guardado Excel Local Ok")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error guardando Excel local: {e}")
            return False

    def _save_to_sqlite(self, units_data: List[Dict], turno: str, fecha: str, hora: str) -> bool:
        """Guarda datos en la base de datos SQLite."""
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                for unit in units_data:
                    cursor.execute('''
                        INSERT INTO registros (fecha, hora, unidad, km, ap, po, turno, jurisdiccion, zona, observaciones)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        fecha,
                        hora,
                        unit['alias'],
                        str(unit['km']),
                        str(unit['ap']),
                        str(unit['po']),
                        ', '.join(unit.get('turnos_seleccionados', [])),
                        unit.get('jurisdiccion', 'SECTORIAL'),
                        unit.get('zona', ''),
                        unit.get('observaciones', '')
                    ))
                conn.commit()
            print(f"[MODELO] Guardado SQLite Ok")
            return True
        except Exception as e:
            print(f"[ERROR] Error guardando SQLite: {e}")
            return False

    def _save_to_cloud(self, units_data: List[Dict], turno: str, fecha: str, hora: str) -> bool:
        """Envía los datos a Google Sheets vía Apps Script Web App."""
        if not self.CLOUD_API_URL:
            print("[MODELO] Cloud API URL no configurada.")
            return False
            
        try:
            payload = {
                "fecha": fecha,
                "hora": hora,
                "turno": turno,
                "units": units_data
            }
            
            logger.info(f"☁️ Iniciando sincronización a: {self.CLOUD_API_URL[:40]}...")
            
            # Usar certifi.where() para asegurar que los certificados SSL sean encontrados en el EXE
            response = requests.post(
                self.CLOUD_API_URL, 
                json=payload, 
                timeout=15, 
                verify=certifi.where()
            )
            
            if response.status_code == 200:
                logger.info("✅ [CLOUD] Sincronización con Google Sheets exitosa")
                return True
            else:
                logger.error(f"❌ [CLOUD] Error en respuesta (HTTP {response.status_code}): {response.text}")
                return False
        except requests.exceptions.SSLError as e:
            logger.error(f"❌ [CLOUD] Error de Certificado SSL: {e}. Intente actualizar el EXE.")
            return False
        except Exception as e:
            logger.error(f"❌ [CLOUD] Fallo de conexión con nube: {e}")
            return False

    
    def _verify_excel_integrity(self, excel_file):
        """Verifica que el archivo Excel tenga las columnas BDMarte correctas."""
        try:
            import pandas as pd
            required_columns = ['FECHA', 'HORA', 'UNIDAD', 'KM', 'AP', 'PO', 'TURNO', 'JURISDICCION', 'OBSERVACIONES']
            if not os.path.exists(excel_file):
                return False
            df = pd.read_excel(excel_file, engine='openpyxl')
            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                print(f"[ERROR] Faltan columnas en Excel Local: {missing}")
                return False
            return True
        except Exception as e:
            print(f"[ERROR] Error verificando integridad: {e}")
            return False

    
    def _save_to_cache(self, units_data: List[Dict], turno: str, filtro_activo: str = "TODAS") -> bool:
        """Guarda datos en caché para acceso rápido."""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'turno': turno,
                'units': units_data,
                'filtro_activo': filtro_activo
            }
            
            # Guardar como último registro
            self.cache.set("last_record", cache_data, persist=True)
            
            # Guardar en historial (limitar a últimos 10 registros)
            history = self.cache.get("records_history", [])
            history.append(cache_data)
            
            # Mantener solo los últimos 10 registros
            if len(history) > 10:
                history = history[-10:]
            
            self.cache.set("records_history", history, persist=True)
            
            print(f"[MODELO] Guardado en caché")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error guardando en caché: {e}")
            return False
    
    def _update_last_save_info(self, units_data: List[Dict], turno: str):
        """Actualiza información del último guardado."""
        try:
            last_save_info = {
                'timestamp': datetime.now().isoformat(),
                'turno': turno,
                'units_count': len(units_data),
                'success': True
            }
            
            self.cache.set("last_save_info", last_save_info, persist=True)
            
        except Exception as e:
            print(f"[ERROR] Error actualizando info de guardado: {e}")
    
    def _check_unsaved_data(self) -> bool:
        """Verifica si hay datos sin guardar en caché."""
        try:
            last_record = self.cache.get("last_record")
            if last_record and last_record.get('units'):
                # Verificar si estos datos ya están en Excel
                excel_data = self.cargar_ultimo_registro()
                if not excel_data or excel_data.get('units_data') != last_record.get('units'):
                    print("[MODELO] Detectados datos sin guardar en Excel")
                    return True
            return False
        except Exception as e:
            print(f"[ERROR] Error verificando datos sin guardar: {e}")
            return False
    
    def _force_save_unsaved_data(self) -> bool:
        """Fuerza el guardado de datos sin guardar antes del cierre."""
        try:
            last_record = self.cache.get("last_record")
            if last_record and last_record.get('units'):
                units_data = last_record.get('units', [])
                turno = last_record.get('turno', '')
                
                if units_data and turno:
                    print("[MODELO] Guardando datos pendientes antes del cierre...")
                    success = self._save_to_excel(units_data, turno)
                    if success:
                        print("[MODELO] Datos pendientes guardados exitosamente")
                        return True
                    else:
                        print("[ERROR] No se pudieron guardar los datos pendientes")
                        return False
            return True  # No hay datos pendientes
        except Exception as e:
            print(f"[ERROR] Error guardando datos pendientes: {e}")
            return False

    def cargar_ultimo_registro(self, force_refresh=False):
        """Carga el último registro, con opción de forzar recarga desde fuentes externas."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Si no se fuerza recarga, intentar usar caché
        if not force_refresh:
            cached = self.cache.get("last_record")
            if cached and cached.get('units_data'):
                logger.info("Using cached last record")
                return cached
        
        # 1. Intentar cargar desde la Nube
        cloud_data = self._cargar_ultimo_registro_cloud()
        if cloud_data and cloud_data.get('units_data'):
            logger.info("Loaded from cloud")
            self.cache.set("last_record", cloud_data, persist=True)
            return cloud_data

        # 2. Intentar cargar desde SQLite (Prioridad Local)
        sqlite_data = self._cargar_ultimo_registro_sqlite()
        if sqlite_data and sqlite_data.get('units_data'):
            logger.info("Loaded from SQLite")
            self.cache.set("last_record", sqlite_data, persist=True)
            return sqlite_data

        # 3. Si falla SQLite, cargar desde Excel Local
        try:
            print(f"[MODELO] Cargando desde respaldo local: {self.EXCEL_BACKUP_FILE}")
            if not os.path.exists(self.EXCEL_BACKUP_FILE):
                return None
            
            df = pd.read_excel(self.EXCEL_BACKUP_FILE, engine='openpyxl')
            if df.empty: return None
            
            # Soporte para ambos formatos de columnas (antiguo y nuevo)
            map_cols = {
                'FECHA': 'FECHA', 'HORA': 'HORA', 'UNIDAD': 'UNIDAD', 
                'KM': 'KM', 'AP': 'AP', 'PO': 'PO', 'TURNO': 'TURNO', 
                'JURISDICCION': 'JURISDICCION'
            }
            # Si no detecta las nuevas, intenta las antiguas con emojis
            if 'FECHA' not in df.columns:
                map_cols = {
                    '📅 FECHA': 'FECHA', '🕰️ HORA': 'HORA', '🚓 UNIDADES': 'UNIDAD',
                    '🚔 KM': 'KM', '📌 A.P': 'AP', '📒 P.O': 'PO', '🕵️‍♂️ TURNO': 'TURNO',
                    '🌙 OBS-TURNO': 'JURISDICCION'
                }

            # Encontrar último timestamp
            col_fecha = next((c for c in df.columns if c in ['FECHA', '📅 FECHA']), None)
            col_hora = next((c for c in df.columns if c in ['HORA', '🕰️ HORA']), None)
            
            if not col_fecha or not col_hora: return None

            df['TempDateTime'] = pd.to_datetime(df[col_fecha].astype(str) + ' ' + df[col_hora].astype(str), errors='coerce', dayfirst=True)
            df = df.dropna(subset=['TempDateTime'])
            
            if df.empty: return None
            
            ultima_fecha_hora = df['TempDateTime'].max()
            ultimo_registro = df[df['TempDateTime'] == ultima_fecha_hora]
            
            units_data = []
            for _, row in ultimo_registro.iterrows():
                # Extraer valores del DataFrame manejando NaN
                def get_cell_value(col_name):
                    val = row.get(map_cols.get(col_name, col_name), '')
                    if pd.isna(val):
                        return ''
                    return str(val).strip()
                
                unit_raw = {
                    'alias': get_cell_value('UNIDAD'),
                    'km': get_cell_value('KM'),
                    'ap': get_cell_value('AP'),
                    'po': get_cell_value('PO'),
                    'turnos_seleccionados': get_cell_value('TURNO'),
                    'jurisdiccion': get_cell_value('JURISDICCION') or 'SECTORIAL'
                }
                
                # Normalizar usando la función auxiliar
                normalized = self._normalize_unit_data(unit_raw)
                if normalized['alias']:  # Solo agregar si tiene alias válido
                    units_data.append(normalized)
            
            if not units_data:
                logger.warning("No valid units found in Excel")
                return None
            
            # Tomar turno del primer registro (puede contener múltiples, pero se usa el principal)
            turno_val = str(ultimo_registro[map_cols['TURNO']].iloc[0]) if pd.notna(ultimo_registro[map_cols['TURNO']].iloc[0]) else ''
            if ',' in turno_val:
                turno_val = turno_val.split(',')[0].strip()
            
            resultado = {
                'units_data': units_data,
                'turno': turno_val,
                'filtro_activo': 'MANUAL'
            }
            logger.info("Loaded from Excel")
            self.cache.set("last_record", resultado, persist=True)
            return resultado
            
        except Exception as e:
            print(f"[ERROR] Error cargando último registro local: {e}")
            return None

    def _cargar_ultimo_registro_cloud(self):
        """Carga el último registro desde la Web App de Google con validación."""
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.CLOUD_API_URL:
            return None
        try:
            response = requests.get(self.CLOUD_API_URL, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Verificar estructura mínima
                if isinstance(data, dict) and 'units_data' in data and isinstance(data['units_data'], list):
                    # Normalizar cada unidad
                    normalized_units = [self._normalize_unit_data(u) for u in data['units_data']]
                    # Filtrar unidades sin alias (datos basura)
                    normalized_units = [u for u in normalized_units if u['alias']]
                    if normalized_units:
                        return {
                            'units_data': normalized_units,
                            'turno': data.get('turno', ''),
                            'filtro_activo': data.get('filtro_activo', 'MANUAL')
                        }
                    else:
                        logger.warning("Cloud data has no valid units after normalization")
                else:
                    logger.warning(f"Unexpected cloud response structure: {type(data)}")
            else:
                logger.error(f"Cloud API returned {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error loading from cloud: {e}")
            return None

    def _cargar_ultimo_registro_sqlite(self):
        """Carga el último registro desde SQLite con normalización."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            if not os.path.exists(self.DB_PATH):
                return None
            
            with sqlite3.connect(self.DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Obtener la fecha y hora del registro más reciente
                cursor.execute("SELECT fecha, hora FROM registros ORDER BY timestamp DESC LIMIT 1")
                row = cursor.fetchone()
                if not row:
                    return None
                
                ultima_fecha = row['fecha']
                ultima_hora = row['hora']
                
                # Obtener todas las unidades de ese mismo instante
                cursor.execute("""
                    SELECT * FROM registros 
                    WHERE fecha = ? AND hora = ?
                """, (ultima_fecha, ultima_hora))
                
                rows = cursor.fetchall()
                units_data = []
                for r in rows:
                    # Normalizar usando la función auxiliar
                    unit_raw = {
                        'alias': r['unidad'],
                        'km': r['km'],
                        'ap': r['ap'],
                        'po': r['po'],
                        'turnos_seleccionados': r['turno'] if r['turno'] else '',
                        'jurisdiccion': r['jurisdiccion']
                    }
                    normalized = self._normalize_unit_data(unit_raw)
                    if normalized['alias']:  # Solo agregar si tiene alias válido
                        units_data.append(normalized)
                
                if not units_data:
                    return None
                
                # Obtener turno principal
                turno_principal = rows[0]['turno'] if rows[0]['turno'] else ''
                # Si el turno contiene comas, tomar el primero
                if ',' in turno_principal:
                    turno_principal = turno_principal.split(',')[0].strip()
                
                return {
                    'units_data': units_data,
                    'turno': turno_principal,
                    'filtro_activo': 'MANUAL'
                }
        except Exception as e:
            logger.error(f"Error loading from SQLite: {e}")
            return None


    # NOTA: _apply_loaded_data ha sido eliminado del modelo.
    # Este método pertenecía a la capa de vista/controlador y accedía a self.view.
    # La lógica de aplicación de datos cargados debe implementarse en el controlador.
                
    def generar_reporte_pdf(self, units_data: List[Dict], turno: str) -> Optional[str]:
        """Genera reporte PDF optimizado."""
        try:
            # Asegurar que existe la carpeta de reportes
            report_dir = "REPORT"
            os.makedirs(report_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"reporte_unidades_{timestamp}.pdf"
            pdf_path = os.path.join(report_dir, pdf_filename)
            
            # Generar contenido del reporte
            content = self._generate_report_content(units_data, turno)
            
            # Guardar como archivo de texto si no se puede generar PDF
            txt_path = pdf_path.replace('.pdf', '.txt')
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"[MODELO] Reporte generado: {txt_path}")
            return txt_path
            
        except Exception as e:
            print(f"[ERROR] Error generando reporte: {e}")
            return None
    
    def _generate_report_content(self, units_data: List[Dict], turno: str) -> str:
        """Genera el contenido del reporte."""
        timestamp = datetime.now()
        fecha = timestamp.strftime("%d/%m/%Y")
        hora = timestamp.strftime("%H:%M:%S")
        
        content = f"""
==============================================
          REPORTE DE UNIDADES - SERENAZGO
==============================================

Fecha: {fecha}
Hora: {hora}
Turno: {turno}
Total de Unidades: {len(units_data)}

==============================================
               DETALLE DE UNIDADES
==============================================

"""
        
        for i, unit in enumerate(units_data, 1):
            content += f"""
Unidad #{i}: {unit['alias']}
--------------------------------
KM: {unit['km']}
AP: {unit['ap']}
PO: {unit['po']}
Turnos: {', '.join(unit.get('turnos_seleccionados', []))}

Observaciones:
"""
            
            # Agregar observaciones
            obs_km, obs_ap, obs_po = self.calcular_observaciones(unit['km'], unit['ap'], unit['po'])
            content += f"  - KM: {obs_km[0]}\n"
            content += f"  - AP: {obs_ap[0]}\n" 
            content += f"  - PO: {obs_po[0]}\n"
            content += "\n"
        
        content += """
==============================================
          FIN DEL REPORTE
==============================================
"""
        
        return content

    def generar_reporte_jpg(self, unidades_info, turno_actual):
        """
        Genera un reporte en formato JPG con orientación horizontal (paisaje) en tamaño A4.
        
        Args:
            unidades_info: Lista de diccionarios con datos de unidades
            turno_actual: Turno principal seleccionado
            
        Returns:
            Tuple: (success, jpg_file_path)
        """
        try:
            # Configuración de la imagen (tamaño A4 horizontal en 300 DPI)
            width, height = 3508, 2480  # 297mm x 210mm en 300 DPI (horizontal)
            background_color = (255, 255, 255)  # Blanco
            image = Image.new('RGB', (width, height), background_color)
            draw = ImageDraw.Draw(image)
            
            # Cargar fuentes (tamaños calculados para 300 DPI)
            try:
                font_path = "arial.ttf"  # Asegúrate de tener esta fuente en tu sistema
                font_title = ImageFont.truetype(font_path, 120)  # Título principal
                font_header = ImageFont.truetype(font_path, 80)  # Encabezados
                font_table_header = ImageFont.truetype(font_path, 70, encoding="unic")  # Encabezados de tabla
                font_table_content = ImageFont.truetype(font_path, 60, encoding="unic")  # Contenido de tabla
            except:
                # Fallback si no se encuentra la fuente
                font_title = ImageFont.load_default()
                font_header = ImageFont.load_default()
                font_table_header = ImageFont.load_default()
                font_table_content = ImageFont.load_default()
            
            # Margen izquierdo y derecho
            margin = 150
            top_margin = 100
            
            # --- LOGO ---
            logo_width = 0
            try:
                # Decodificar el logo desde la constante Base64
                logo_data = base64.b64decode(LOGO_BASE64)
                logo = Image.open(io.BytesIO(logo_data))
                
                # Redimensionar logo (Ajustar a una altura fija para no sobrepasar la línea)
                logo_height = 480
                logo_width = int((logo.size[0] / logo.size[1]) * logo_height)
                logo = logo.resize((logo_width, logo_height), Image.LANCZOS)
                
                # Posicionar logo en la esquina superior izquierda
                logo_x = margin
                logo_y = top_margin
                image.paste(logo, (logo_x, logo_y), logo if logo.mode == 'RGBA' else None)
            except Exception as e:
                print(f"Error al procesar logo: {str(e)}")
            
            # --- TÍTULOS ---
            # Configurar colores
            title_color = (0, 0, 0)  # Negro
            blue_color = (0, 56, 147)  # Azul oscuro
            orange_color = (237, 125, 49)  # Naranja
            
            # Obtener fecha formateada (MODIFICACIÓN: Usar datetime.now() directamente)
            ahora = datetime.now()  # <-- Usar datetime local directamente
            dias_semana = {
                0: "LUNES",
                1: "MARTES",
                2: "MIÉRCOLES",
                3: "JUEVES",
                4: "VIERNES",
                5: "SÁBADO",
                6: "DOMINGO"
            }
            nombre_dia = dias_semana.get(ahora.weekday(), "DIA")
            fecha_formateada = f"{nombre_dia}, {ahora.day} DE {ahora.strftime('%B').upper()} DE {ahora.year}"
            
            # Posiciones iniciales (empezamos después del logo)
            y_position = top_margin + 50
            x_position = margin + logo_width + 100
            
            # Título principal - TALARA (a la derecha del logo)
            title_text = "TALARA"
            draw.text((x_position, y_position), title_text, 
                     fill=blue_color, font=font_title)
            y_position += 120
            
            # Fecha (debajo del título)
            date_text = f"{fecha_formateada}"
            draw.text((x_position, y_position), date_text,
                     fill=title_color, font=font_header)
            y_position += 100
            
            # KM y horas
            hora_final = self._get_hora_final_turno(turno_actual)
            km_text = f"KM - 00:00 HRS / {hora_final} HORAS"
            draw.text((x_position, y_position), km_text,
                     fill=title_color, font=font_header)
            y_position += 100
            
            # Turno
            turno_text = f"TURNO: {turno_actual}"
            draw.text((x_position, y_position), turno_text,
                     fill=blue_color, font=font_header)
            y_position += 150
            
            # Separador (línea azul gruesa)
            draw.line([(margin, y_position), (width-margin, y_position)], fill=blue_color, width=8)
            y_position += 100
            
            # --- TABLAS ---
            # Configuración de márgenes y columnas
            margin = 150
            width = 3208 + 2 * 150 # Total base 3508
            col_widths = [400, 300, 300, 300, 600, 500, 808]  # 7 columnas: UNIDAD, KM, AP, PO, TURNO, JURISDICCION, ZONA (808 para llenar el ancho exacto)
            # Separar camionetas y autos (mostrar TODAS las unidades seleccionadas en la imagen)
            camionetas_data = []
            autos_data = []
            for data in unidades_info:
                # Incluir todas las unidades seleccionadas en la imagen (no filtrar por turno)
                unidad_real = self.ALIAS_UNIDADES.get(data['alias'], data['alias'])
                if unidad_real in self.CAMIONETAS:
                    camionetas_data.append(data)
                elif unidad_real in self.AUTOS:
                    autos_data.append(data)
            
            # Función auxiliar para limpiar alias (remover emojis para JPG)
            def clean_alias_for_jpg(alias):
                """Remueve emojis del alias para mostrar en JPG."""
                # Remover emojis de camioneta y auto
                return alias.replace('🚙 ', '').replace('🚘 ', '')
            
            # --- TABLA CAMIONETAS ---
            if camionetas_data:
                # Encabezado de sección (centrado)
                section_title = "CAMIONETAS PICK-UP"
                text_width = draw.textlength(section_title, font=font_header)
                draw.text(((width - text_width) // 2, y_position), section_title, 
                         fill=blue_color, font=font_header)
                y_position += 120
                
                # Encabezados de tabla
                headers = ["UNIDAD", "KM", "AP", "PO", "TURNO", "JURISDICCION", "ZONA"]
                                
                # Dibujar fondo de encabezado (azul)
                draw.rectangle([(margin, y_position), (width-margin, y_position+90)], fill=blue_color)
                
                # Dibujar texto de encabezado (blanco en negrita)
                x_pos = margin
                for i, (header, col_width) in enumerate(zip(headers, col_widths)):
                    # Usamos una fuente con negrita para los encabezados
                    draw.text((x_pos + col_width//2, y_position+45), header, 
                             fill="white", font=font_table_header, anchor="mm")
                    if i < len(headers)-1:  # No dibujar línea después del último encabezado
                        draw.line([(x_pos+col_width, y_position), (x_pos+col_width, y_position+90)], 
                                 fill="white", width=3)
                    x_pos += col_width
                y_position += 90
                
                # Datos de camionetas
                for i, data in enumerate(camionetas_data):
                    unidad_real = self.ALIAS_UNIDADES.get(data['alias'], data['alias'])
                    
                    # Color de fila alternado (azul claro/blanco)
                    fill_color = (230, 240, 255) if i % 2 == 0 else (255, 255, 255)
                    draw.rectangle([(margin, y_position), (width-margin, y_position+90)], fill=fill_color)
                    
                    # Dibujar bordes de celda
                    draw.rectangle([(margin, y_position), (width-margin, y_position+90)], outline=(200, 200, 200), width=2)
                    
                    x_pos = margin
                    # UNIDAD (emoji removido para compatibilidad con PIL)
                    alias_limpio = clean_alias_for_jpg(data['alias'])
                    draw.text((x_pos + col_widths[0]//2, y_position+45), alias_limpio,
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[0], y_position), (x_pos+col_widths[0], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[0]
                    
                    # PLACA - COLUMNA ELIMINADA (redundante con UNIDAD)
                    # El código de PLACA ha sido removido ya que UNIDAD ya muestra "1 EUI-621"
                    
                    # KM (ahora en índice 1)
                    km = str(data['km']) if data['km'] else "---"
                    draw.text((x_pos + col_widths[1]//2, y_position+45), km, 
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[1], y_position), (x_pos+col_widths[1], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[1]
                    
                    # AP (ahora en índice 2)
                    ap = str(data['ap']) if data['ap'] else "---"
                    draw.text((x_pos + col_widths[2]//2, y_position+45), ap, 
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[2], y_position), (x_pos+col_widths[2], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[2]
                    
                    # PO (con fondo amarillo, ahora en índice 3)
                    po = str(data['po']) if data['po'] else "---"
                    draw.rectangle([(x_pos, y_position), (x_pos+col_widths[3], y_position+90)], fill=(255, 255, 153))
                    draw.text((x_pos + col_widths[3]//2, y_position+45), po, 
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[3], y_position), (x_pos+col_widths[3], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[3]
                    
                    # TURNO (ahora en índice 4)
                    turnos = ', '.join(data['turnos_seleccionados']) if data['turnos_seleccionados'] else "---"
                    draw.text((x_pos + col_widths[4]//2, y_position+45), turnos, 
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[4], y_position), (x_pos+col_widths[4], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[4]
                    
                    # JURISDICCION (ahora en índice 5)
                    jurisdiccion = data.get('jurisdiccion', 'SECTORIAL')
                    draw.text((x_pos + col_widths[5]//2, y_position+45), jurisdiccion, 
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[5], y_position), (x_pos+col_widths[5], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[5]
                    
                    # ZONA (índice 6) con color según zona - rellena hasta el borde derecho de la tabla
                    zona = data.get('zona', '')
                    zona_colors = {
                        'NORTE': (149, 82, 189),    # Morado
                        'SUR':   (230, 115, 0),      # Naranja
                        'CENTRO': (34, 120, 34),     # Verde oscuro
                        'ENACE': (204, 170, 0),      # Amarillo/Ocre
                    }
                    zona_bg = zona_colors.get(zona, (240, 240, 240))
                    zona_fg = (255, 255, 255) if zona in ('NORTE', 'SUR', 'CENTRO') else (0, 0, 0)
                    draw.rectangle([(x_pos, y_position), (width-margin, y_position+90)], fill=zona_bg)
                    draw.text((x_pos + (width-margin-x_pos)//2, y_position+45), zona, 
                             fill=zona_fg, font=font_table_content, anchor="mm")
                    
                    y_position += 90
                
                # Espacio después de la tabla
                y_position += 60
            
            # --- TABLA AUTOS ---
            if autos_data:
                # Separador (línea naranja gruesa)
                draw.line([(margin, y_position), (width-margin, y_position)], fill=orange_color, width=8)
                y_position += 80
                
                # Encabezado de sección (centrado)
                section_title = "AUTOS SEDAN"
                text_width = draw.textlength(section_title, font=font_header)
                draw.text(((width - text_width) // 2, y_position), section_title, 
                         fill=orange_color, font=font_header)
                y_position += 120
                
                # Encabezados de tabla (misma estructura que camionetas)
                headers = ["UNIDAD", "KM", "AP", "PO", "TURNO", "JURISDICCION", "ZONA"]
                
                # Dibujar fondo de encabezado (naranja)
                draw.rectangle([(margin, y_position), (width-margin, y_position+90)], fill=orange_color)
                
                # Dibujar texto de encabezado (blanco en negrita)
                x_pos = margin
                for i, (header, col_width) in enumerate(zip(headers, col_widths)):
                    draw.text((x_pos + col_width//2, y_position+45), header, 
                             fill="white", font=font_table_header, anchor="mm")
                    if i < len(headers)-1:
                        draw.line([(x_pos+col_width, y_position), (x_pos+col_width, y_position+90)], 
                                 fill="white", width=3)
                    x_pos += col_width
                y_position += 90
                
                # Datos de autos
                for i, data in enumerate(autos_data):
                    unidad_real = self.ALIAS_UNIDADES.get(data['alias'], data['alias'])
                    
                    # Color de fila alternado (naranja claro/blanco)
                    fill_color = (255, 230, 204) if i % 2 == 0 else (255, 255, 255)
                    draw.rectangle([(margin, y_position), (width-margin, y_position+90)], fill=fill_color)
                    
                    # Dibujar bordes de celda
                    draw.rectangle([(margin, y_position), (width-margin, y_position+90)], outline=(200, 200, 200), width=2)
                    
                    x_pos = margin
                    # UNIDAD (emoji removido para compatibilidad con PIL)
                    alias_limpio = clean_alias_for_jpg(data['alias'])
                    draw.text((x_pos + col_widths[0]//2, y_position+45), alias_limpio,
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[0], y_position), (x_pos+col_widths[0], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[0]
                    
                    # PLACA - COLUMNA ELIMINADA (redundante con UNIDAD)
                    # El código de PLACA ha sido removido ya que UNIDAD ya muestra "1 EUI-621"
                    
                    # KM (ahora en índice 1)
                    km = str(data['km']) if data['km'] else "---"
                    draw.text((x_pos + col_widths[1]//2, y_position+45), km, 
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[1], y_position), (x_pos+col_widths[1], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[1]
                    
                    # AP (ahora en índice 2)
                    ap = str(data['ap']) if data['ap'] else "---"
                    draw.text((x_pos + col_widths[2]//2, y_position+45), ap, 
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[2], y_position), (x_pos+col_widths[2], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[2]
                    
                    # PO (con fondo amarillo, ahora en índice 3)
                    po = str(data['po']) if data['po'] else "---"
                    draw.rectangle([(x_pos, y_position), (x_pos+col_widths[3], y_position+90)], fill=(255, 255, 153))
                    draw.text((x_pos + col_widths[3]//2, y_position+45), po, 
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[3], y_position), (x_pos+col_widths[3], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[3]
                    
                    # TURNO (ahora en índice 4)
                    turnos = ', '.join(data['turnos_seleccionados']) if data['turnos_seleccionados'] else "---"
                    draw.text((x_pos + col_widths[4]//2, y_position+45), turnos, 
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[4], y_position), (x_pos+col_widths[4], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[4]
                    
                    # JURISDICCION (ahora en índice 5)
                    jurisdiccion = data.get('jurisdiccion', 'SECTORIAL')
                    draw.text((x_pos + col_widths[5]//2, y_position+45), jurisdiccion, 
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[5], y_position), (x_pos+col_widths[5], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[5]
                    
                    # ZONA (índice 6) con color según zona
                    zona = data.get('zona', '')
                    zona_colors = {
                        'NORTE': (149, 82, 189),    # Morado
                        'SUR':   (230, 115, 0),      # Naranja
                        'CENTRO': (34, 120, 34),     # Verde oscuro
                        'ENACE': (204, 170, 0),      # Amarillo/Ocre
                    }
                    zona_bg = zona_colors.get(zona, (240, 240, 240))
                    zona_fg = (255, 255, 255) if zona in ('NORTE', 'SUR', 'CENTRO') else (0, 0, 0)
                    draw.rectangle([(x_pos, y_position), (width-margin, y_position+90)], fill=zona_bg)
                    draw.text((x_pos + (width-margin-x_pos)//2, y_position+45), zona, 
                             fill=zona_fg, font=font_table_content, anchor="mm")
                    
                    y_position += 90
            
            # Guardar la imagen JPG (alta calidad)
            os.makedirs("REPORT", exist_ok=True)
            report_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            jpg_file = os.path.join("REPORT", f"reporte_serenazgo_{report_timestamp}.jpg")
            image.save(jpg_file, "JPEG", quality=95, dpi=(300, 300))
                                       
            return True, jpg_file
            
        except Exception as e:
            print(f"Error al generar reporte JPG: {str(e)}")
            return False, f"Error al generar reporte JPG: {str(e)}"

    def _get_hora_final_turno(self, turno):
        """Helper para obtener la hora final de un turno."""
        if turno == "DÍA":
            return "14:00"
        elif turno == "TARDE":
            return "22:00"
        elif turno == "NOCHE":
            return "06:00"
        else:
            return "--:--"

    

    def get_cache_metrics(self) -> Dict:
        """Obtiene métricas del sistema de caché."""
        try:
            return self.cache.get_metrics().to_dict()
        except Exception as e:
            print(f"[ERROR] Error obteniendo métricas de caché: {e}")
            return {}

    def cleanup_old_data(self, days_old: int = 30) -> Dict[str, int]:
        """Limpia datos antiguos del sistema."""
        try:
            cleaned = {
                'cache_entries': 0,
                'json_files': 0
            }
            
            # Limpiar caché
            cache_result = self.cache.cleanup(days_old)
            cleaned['cache_entries'] = cache_result.get('disk_deleted', 0)
            
            # Limpiar archivos JSON antiguos
            json_dir = "data_json"
            if os.path.exists(json_dir):
                cutoff_time = time.time() - (days_old * 24 * 3600)
                for filename in os.listdir(json_dir):
                    filepath = os.path.join(json_dir, filename)
                    if os.path.getmtime(filepath) < cutoff_time:
                        os.remove(filepath)
                        cleaned['json_files'] += 1
            
            print(f"[MODELO] Limpieza completada: {cleaned}")
            return cleaned
            
        except Exception as e:
            print(f"[ERROR] Error en limpieza: {e}")
            return {'cache_entries': 0, 'json_files': 0}

    def shutdown(self):
        """Cierra el modelo de forma ordenada."""
        try:
            # 1. Detener nuevas operaciones en el caché
            if hasattr(self.cache, 'pause'):
                self.cache.pause()  # Método hipotético - deberías implementarlo

            # 2. Guardar configuración actual
            config_to_save = {
                'version': getattr(self, 'version', '2.0'),
                'last_update': datetime.now().isoformat(),
                'validation_rules': getattr(self, 'validation_rules', {})
            }
            if hasattr(self.cache, 'set_sync'):
                self.cache.set_sync("model_config", config_to_save)  # Versión síncrona
            
            # 3. Verificar y guardar datos pendientes
            try:
                # Verificar si hay datos sin guardar
                if self._check_unsaved_data():
                    print("[MODELO] Detectados datos sin guardar, intentando guardar...")
                    if not self._force_save_unsaved_data():
                        print("[ADVERTENCIA] No se pudieron guardar los datos pendientes")
            except Exception as e:
                print(f"[ADVERTENCIA] Error en proceso de guardado de cierre: {e}")
            
            # 4. Cerrar caché
            if hasattr(self.cache, 'shutdown'):
                self.cache.shutdown()
            
            print("[MODELO] Cerrado correctamente")
            
        except Exception as e:
            print(f"[ERROR] Error cerrando modelo: {e}")
    
    def get_img_folder(self):
        return self.IMG_FOLDER
    
    def vaciar_excel_registros_alternativo(self):
        """Método alternativo para vaciar Excel que recrea el archivo (más robusto para .exe)."""
        try:
            print(f"[VACIAR BD ALT] Iniciando método alternativo...")
            print(f"[VACIAR BD ALT] Ruta del archivo: {self.EXCEL_BACKUP_FILE}")
            
            # Crear respaldo antes de proceder
            backup_file = self.EXCEL_BACKUP_FILE + ".backup_" + datetime.now().strftime('%Y%m%d_%H%M%S')
            if os.path.exists(self.EXCEL_BACKUP_FILE):
                import shutil
                shutil.copy2(self.EXCEL_BACKUP_FILE, backup_file)
                print(f"[VACIAR BD ALT] Respaldo creado: {backup_file}")
            
            # Crear nuevo archivo Excel vacío con encabezados
            print(f"[VACIAR BD ALT] Creando nuevo archivo Excel...")
            
            # Crear DataFrame vacío con encabezados
            headers = ['🚓 UNIDADES', '🚔 KM', '📌 A.P', '📒 P.O', '🕵️‍♂️ TURNO', '🌙 OBS-TURNO', '🕰️ HORA', '📅 FECHA', '✍ OBSERVACIONES ⛑']
            df = pd.DataFrame(columns=headers)
            
            # Guardar con formato usando pandas
            with pd.ExcelWriter(self.EXCEL_BACKUP_FILE, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Registro de Unidades')
                
                # Obtener el workbook y worksheet
                workbook = writer.book
                worksheet = writer.sheets['Registro de Unidades']
                
                # Aplicar formato a encabezados
                from openpyxl.styles import Font, Alignment, PatternFill
                
                header_font = Font(bold=True, color="FFFFFF")
                header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                
                for col in range(1, len(headers) + 1):
                    cell = worksheet.cell(row=1, column=col)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal="center")
            
            print(f"[VACIAR BD ALT] Archivo recreado exitosamente")
            
            # Verificar que se creó correctamente
            if os.path.exists(self.EXCEL_BACKUP_FILE):
                file_size = os.path.getsize(self.EXCEL_BACKUP_FILE)
                print(f"[VACIAR BD ALT] Archivo creado. Tamaño: {file_size} bytes")
                
                # Verificar contenido
                try:
                    df_verify = pd.read_excel(self.EXCEL_BACKUP_FILE, engine='openpyxl')
                    print(f"[VACIAR BD ALT] Verificación: {len(df_verify)} filas (solo encabezados)")
                    
                    if len(df_verify) == 0:
                        print(f"[VACIAR BD ALT] ✅ Vaciado completado exitosamente")
                        
                        # Limpiar respaldo si todo salió bien
                        if os.path.exists(backup_file):
                            os.remove(backup_file)
                            print(f"[VACIAR BD ALT] Respaldo eliminado")
                        
                        return True
                    else:
                        print(f"[VACIAR BD ALT] ⚠️ El archivo aún tiene {len(df_verify)} filas")
                        return False
                        
                except Exception as e:
                    print(f"[ERROR] Error verificando archivo recreado: {e}")
                    return False
            else:
                print(f"[ERROR] El archivo no existe después de recrear")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error en método alternativo: {e}")
            import traceback
            traceback.print_exc()
            
            # Intentar restaurar respaldo si existe
            if 'backup_file' in locals() and os.path.exists(backup_file):
                try:
                    import shutil
                    shutil.copy2(backup_file, self.EXCEL_BACKUP_FILE)
                    print(f"[VACIAR BD ALT] Respaldo restaurado después del error")
                except:
                    pass
            
            return False

    def vaciar_excel_registros(self):
        """Elimina todos los registros del archivo Excel dejando solo los encabezados (con emojis y estilos)."""
        try:
            print(f"[DEBUG] Vaciando archivo Excel: {self.EXCEL_BACKUP_FILE}")
            import openpyxl
            from openpyxl.styles import Font, Alignment, PatternFill
            
            print(f"[VACIAR BD] Iniciando proceso de vaciado...")
            print(f"[VACIAR BD] Ruta del archivo: {self.EXCEL_BACKUP_FILE}")
            
            # Verificar si el archivo existe
            if not os.path.exists(self.EXCEL_BACKUP_FILE):
                print(f"[VACIAR BD] Archivo no existe, inicializando...")
                self._initialize_excel_backup()
            
            # Verificar permisos de escritura
            if not os.access(self.EXCEL_BACKUP_FILE, os.W_OK):
                print(f"[ERROR] No hay permisos de escritura en: {self.EXCEL_BACKUP_FILE}")
                print(f"[VACIAR BD] Intentando método alternativo...")
                return self.vaciar_excel_registros_alternativo()
            
            print(f"[VACIAR BD] Cargando archivo Excel...")
            wb = openpyxl.load_workbook(self.EXCEL_BACKUP_FILE)
            ws = wb.active
            
            print(f"[VACIAR BD] Filas antes de vaciar: {ws.max_row}")
            
            # Encabezados oficiales (Nuevos, sin emojis para máxima compatibilidad)
            headers = ['FECHA', 'HORA', 'UNIDAD', 'KM', 'AP', 'PO', 'TURNO', 'JURISDICCION', 'OBSERVACIONES']
            
            # Borra todas las filas excepto la primera
            if ws.max_row > 1:
                print(f"[VACIAR BD] Eliminando {ws.max_row - 1} filas de datos...")
                ws.delete_rows(2, ws.max_row + 100) # Asegurar limpieza profunda
            
            # Reaplicar encabezados y estilos
            print(f"[VACIAR BD] Aplicando encabezados y estilos oficiales...")
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
            
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center")
            
            # Limpiar cualquier residuo después de los encabezados
            if ws.max_row > 1:
                for row in ws.iter_rows(min_row=2):
                    for cell in row:
                        cell.value = None

            print(f"[VACIAR BD] Guardando archivo...")
            wb.save(self.EXCEL_BACKUP_FILE)
            wb.close()
            
            # Verificar que se guardó correctamente
            print(f"[VACIAR BD] Verificando archivo guardado...")
            if os.path.exists(self.EXCEL_BACKUP_FILE):
                file_size = os.path.getsize(self.EXCEL_BACKUP_FILE)
                print(f"[VACIAR BD] Archivo guardado exitosamente. Tamaño: {file_size} bytes")
                
                # Verificar que solo tiene encabezados
                try:
                    df_verify = pd.read_excel(self.EXCEL_BACKUP_FILE, engine='openpyxl')
                    print(f"[VACIAR BD] Verificación: {len(df_verify)} filas (solo encabezados)")
                    if len(df_verify) == 0:
                        print(f"[VACIAR BD] ✅ Vaciado completado exitosamente")
                        return True
                    else:
                        print(f"[VACIAR BD] ⚠️ El archivo aún tiene {len(df_verify)} filas")
                        print(f"[VACIAR BD] Intentando método alternativo...")
                        return self.vaciar_excel_registros_alternativo()
                except Exception as e:
                    print(f"[ERROR] Error verificando archivo después del vaciado: {e}")
                    print(f"[VACIAR BD] Intentando método alternativo...")
                    return self.vaciar_excel_registros_alternativo()
            else:
                print(f"[ERROR] El archivo no existe después de guardar")
                print(f"[VACIAR BD] Intentando método alternativo...")
                return self.vaciar_excel_registros_alternativo()
                
        except PermissionError as e:
            print(f"[ERROR] Error de permisos al vaciar Excel: {e}")
            print(f"[ERROR] El archivo puede estar abierto en Excel o no tienes permisos")
            print(f"[VACIAR BD] Intentando método alternativo...")
            return self.vaciar_excel_registros_alternativo()
        except Exception as e:
            print(f"[ERROR] Error vaciando Excel: {e}")
            import traceback
            traceback.print_exc()
            return False

    def vaciar_registros_nube(self) -> bool:
        """Envía una petición a la Web App de Google para vaciar la hoja de cálculo."""
        if not self.CLOUD_API_URL:
            print("[ERROR] URL de Cloud API no configurada")
            return False
            
        try:
            payload = {
                "action": "clear",
                "password": "password&clave" # Opcional: validación extra en el script
            }
            
            print(f"[MODELO] Solicitando vaciado de base de datos en la nube...")
            response = requests.post(self.CLOUD_API_URL, json=payload, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    print("[MODELO] ✅ Base de datos en la nube vaciada exitosamente")
                    return True
                else:
                    print(f"[ERROR] Error de Cloud API: {result.get('message')}")
                    return False
            else:
                print(f"[ERROR] Error HTTP en Cloud API: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Excepción al vaciar registros en la nube: {e}")
            return False

    def _create_excel_backup(self) -> bool:
        """Crea un respaldo automático del archivo Excel antes de guardar."""
        try:
            if not os.path.exists(self.EXCEL_BACKUP_FILE):
                return True  # No hay archivo para respaldar
            
            # Crear carpeta de respaldos si no existe
            backup_dir = "backups_excel"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Generar nombre de respaldo con timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_dir, f"unidades_registro_backup_{timestamp}.xlsx")
            
            # Copiar archivo
            import shutil
            shutil.copy2(self.EXCEL_BACKUP_FILE, backup_file)
            
            # Mantener solo los últimos 10 respaldos
            backup_files = glob.glob(os.path.join(backup_dir, "unidades_registro_backup_*.xlsx"))
            if len(backup_files) > 10:
                backup_files.sort()
                for old_backup in backup_files[:-10]:
                    os.remove(old_backup)
            
            print(f"[MODELO] Respaldo automático creado: {backup_file}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error creando respaldo automático: {e}")
            return False

# Alias para compatibilidad
Model = OptimizedModel

LOGO_BASE64 = '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'
