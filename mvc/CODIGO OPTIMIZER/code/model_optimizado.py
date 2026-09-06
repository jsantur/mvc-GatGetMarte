# model.py (versión ULTRA-OPTIMIZADA con validación robusta) - CORREGIDO
import hashlib
import locale
import math
import time
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
import os
import json
from pathlib import Path
import pickle
import sys
from datetime import datetime, timedelta
import threading
import shutil
from typing import Dict, List, Tuple, Optional, Any
from cache import OptimizedCacheManager, CacheConfig

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

def resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso, funciona para desarrollo y para PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_base_path():
    """Obtiene la ruta base correcta tanto en desarrollo como en ejecutable."""
    try:
        if getattr(sys, 'frozen', False):
            # Si estamos en un ejecutable PyInstaller, usar el directorio del ejecutable
            base_path = os.path.dirname(sys.executable)
        else:
            # Si estamos en desarrollo o no es un ejecutable PyInstaller
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        return base_path
    except Exception as e:
        print(f"[ERROR] Error obteniendo ruta base: {e}")
        # Fallback al directorio actual
        return os.getcwd()

class UnidadesFileManager:
    """Gestor robusto para el archivo unidades.txt con validación y recuperación automática."""
    
    def __init__(self, file_path: str = "unidades.txt"):
        self.file_path = file_path
        self.template_path = f"{file_path}.template"
        self._lock = threading.Lock()
        
        # Plantilla por defecto para crear el archivo si no existe
        self.default_template = [
            "H1 / EUI-621;EUI-621;PICKUP",
            "H2 / EUI-682;EUI-682;PICKUP", 
            "H3 / EUI-683;EUI-683;PICKUP",
            "H4 / EUI-646;EUI-646;PICKUP",
            "H5 / EUI-685;EUI-685;PICKUP",
            "H6 / EUI-686;EUI-686;PICKUP",
            "H7 / EUI-679;EUI-679;PICKUP",
            "H8 / EUI-680;EUI-680;PICKUP",
            "H9 / EUI-645;EUI-645;AUTO",
            "H10 / EUI-647;EUI-647;AUTO",
            "H11 / EUI-668;EUI-668;AUTO"
        ]
    
    def ensure_file_exists(self) -> bool:
        """Asegura que el archivo unidades.txt existe y es válido."""
        with self._lock:
            try:
                # Si el archivo existe, validarlo
                if os.path.exists(self.file_path):
                    if self.validate_file():
                        return True
                    else:
                        print(f"[ADVERTENCIA] Archivo {self.file_path} existe pero es inválido")
                        return self._recover_or_create_file()
                else:
                    print(f"[INFORMACIÓN] Archivo {self.file_path} no existe, creando desde plantilla")
                    return self._create_from_template()
                    
            except Exception as e:
                print(f"[ERROR] Error validando archivo unidades: {e}")
                return self._recover_or_create_file()
    
    def validate_file(self) -> bool:
        """Valida que el archivo unidades.txt tiene el formato correcto."""
        try:
            if not os.path.exists(self.file_path):
                return False
            
            # Verificar que el archivo no esté vacío
            if os.path.getsize(self.file_path) == 0:
                print("[ADVERTENCIA] Archivo unidades.txt está vacío")
                return False
            
            # Validar formato de cada línea
            valid_lines = 0
            with open(self.file_path, 'r', encoding='utf-8') as f:
                for line_num, linea in enumerate(f, 1):
                    linea = linea.strip()
                    if not linea:  # Ignorar líneas vacías
                        continue
                    
                    if not self._validate_line_format(linea):
                        print(f"[ERROR] Línea {line_num} tiene formato inválido: {linea}")
                        return False
                    
                    valid_lines += 1
            
            if valid_lines == 0:
                print("[ADVERTENCIA] No se encontraron líneas válidas en unidades.txt")
                return False
            
            print(f"[ÉXITO] Archivo unidades.txt validado correctamente ({valid_lines} unidades)")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error validando archivo: {e}")
            return False
    
    def _validate_line_format(self, line: str) -> bool:
        """Valida que una línea tenga el formato correcto: 'alias;codigo;tipo'."""
        try:
            if ';' not in line:
                return False
            
            parts = line.split(';')
            if len(parts) != 3:
                return False
            
            alias, codigo, tipo = parts
            
            # Validar que los campos no estén vacíos
            if not alias.strip() or not codigo.strip() or not tipo.strip():
                return False
            
            # Validar que el tipo sea válido
            if tipo.strip().upper() not in ['PICKUP', 'AUTO']:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _recover_or_create_file(self) -> bool:
        """Intenta recuperar o crear archivo nuevo."""
        try:
            # Si no hay archivo válido, crear desde plantilla
            return self._create_from_template()
            
        except Exception as e:
            print(f"[ERROR] Error en recuperación: {e}")
            return self._create_from_template()
    
    def _create_from_template(self) -> bool:
        """Crea el archivo unidades.txt desde la plantilla."""
        try:
            print(f"[INFORMACIÓN] Creando archivo {self.file_path} desde plantilla por defecto")
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                for line in self.default_template:
                    f.write(line + '\n')
            
            # Validar el archivo creado
            if self.validate_file():
                print("[ÉXITO] Archivo unidades.txt creado exitosamente desde plantilla")
                return True
            else:
                print("[ERROR] Error validando archivo creado desde plantilla")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error creando archivo desde plantilla: {e}")
            return False
    
    def load_units(self) -> Tuple[Dict[str, str], set, set, List[str]]:
        """Carga las unidades desde el archivo validado."""
        alias_unidades = {}
        camionetas = set()
        autos = set()
        unidades_disponibles = []
        
        try:
            # Asegurar que el archivo existe y es válido
            if not self.ensure_file_exists():
                raise Exception("No se pudo crear o validar el archivo unidades.txt")
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                for linea in f:
                    linea = linea.strip()
                    if linea and ';' in linea:
                        try:
                            partes = linea.split(';')
                            if len(partes) >= 3:
                                alias = partes[0].strip()
                                codigo = partes[1].strip()
                                tipo = partes[2].strip().upper()
                                
                                # Mapear alias a código
                                alias_unidades[alias] = codigo
                                unidades_disponibles.append(alias)
                                
                                # Clasificar por tipo
                                if tipo == 'PICKUP':
                                    camionetas.add(codigo)
                                elif tipo == 'AUTO':
                                    autos.add(codigo)
                                else:
                                    print(f"[ADVERTENCIA] Tipo desconocido '{tipo}' para unidad {alias}")
                                    
                        except Exception as e:
                            print(f"[ERROR] Error procesando línea '{linea}': {e}")
                            continue
            
            print(f"[ÉXITO] Cargadas {len(unidades_disponibles)} unidades: "
                  f"{len(camionetas)} pickup, {len(autos)} autos")
            
            return alias_unidades, camionetas, autos, unidades_disponibles
            
        except Exception as e:
            print(f"[ERROR] Error cargando unidades: {e}")
            # Retornar configuración por defecto en caso de error
            return self._get_default_configuration()
    
    def _get_default_configuration(self) -> Tuple[Dict[str, str], set, set, List[str]]:
        """Retorna configuración por defecto en caso de error."""
        print("[ADVERTENCIA] Usando configuración por defecto")
        
        alias_unidades = {}
        camionetas = set()
        autos = set()
        unidades_disponibles = []
        
        for line in self.default_template:
            try:
                alias, codigo, tipo = line.split(';')
                alias_unidades[alias] = codigo
                unidades_disponibles.append(alias)
                
                if tipo == 'PICKUP':
                    camionetas.add(codigo)
                elif tipo == 'AUTO':
                    autos.add(codigo)
            except:
                continue
        
        return alias_unidades, camionetas, autos, unidades_disponibles
    
    def add_unit(self, alias: str, codigo: str, tipo: str) -> bool:
        """Agrega una nueva unidad al archivo."""
        try:
            with self._lock:
                # Validar parámetros
                if not alias.strip() or not codigo.strip() or tipo.upper() not in ['PICKUP', 'AUTO']:
                    return False
                
                # Agregar nueva línea
                new_line = f"{alias.strip()};{codigo.strip()};{tipo.upper()}"
                
                with open(self.file_path, 'a', encoding='utf-8') as f:
                    f.write('\n' + new_line)
                
                # Validar archivo modificado
                if self.validate_file():
                    print(f"[ÉXITO] Unidad agregada: {alias}")
                    return True
                else:
                    return False
                    
        except Exception as e:
            print(f"[ERROR] Error agregando unidad: {e}")
            return False

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

        # Gestor de archivo de unidades
        self.units_manager = UnidadesFileManager("unidades.txt")
        
        # Cargar unidades desde archivo con validación robusta
        self._cargar_unidades_desde_archivo()
                        
        self.IMG_FOLDER = "IMG"
        self.LINK_GEOSATELITAL = "https://panel.geosatelital.com/dashboard"
        self.LINK_SIPCOP = "https://seguridadciudadana.mininter.gob.pe/sipcop-m/reportes/mapa-recorrido-vehiculo"
        
        # Configurar locale para fechas
        self._setup_locale()

        # Configurar archivo de respaldo Excel
        self.EXCEL_BACKUP_FILE = os.path.join(get_base_path(), "unidades_registro.xlsx")
        self._initialize_excel_backup()
    
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
        """Carga las unidades desde el archivo con validación robusta."""
        try:
            with self._data_lock:
                # Usar el gestor de archivos para carga robusta
                (self.ALIAS_UNIDADES, self.CAMIONETAS, 
                 self.AUTOS, self.UNIDADES_DISPONIBLES) = self.units_manager.load_units()
                
                # Guardar en caché para acceso rápido
                self.cache.set("units_data", {
                    'alias_unidades': self.ALIAS_UNIDADES,
                    'camionetas': list(self.CAMIONETAS),
                    'autos': list(self.AUTOS), 
                    'unidades_disponibles': self.UNIDADES_DISPONIBLES
                }, persist=True)
                
                print(f"[MODELO] Unidades cargadas y almacenadas en caché")
                
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
                
                # Encabezados
                headers = ['Fecha', 'Hora', 'Turno', 'Unidad', 'KM', 'AP', 'PO', 'Turnos', 'Observaciones']
                for col, header in enumerate(headers, 1):
                    worksheet.cell(row=1, column=col, value=header)
                
                # Aplicar estilo a encabezados
                header_font = Font(bold=True, color="FFFFFF")
                header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                
                for col in range(1, len(headers) + 1):
                    cell = worksheet.cell(row=1, column=col)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal="center")
                
                workbook.save(self.EXCEL_BACKUP_FILE)
                print(f"[MODELO] Archivo Excel inicializado: {self.EXCEL_BACKUP_FILE}")
                
        except Exception as e:
            print(f"[ERROR] Error inicializando archivo Excel: {e}")

    def get_unit_info(self) -> Tuple[List[str], Dict[str, str], set, set]:
        """Obtiene información de unidades con caché optimizado."""
        cache_key = "unit_info_complete"
        cached_data = self.cache.get(cache_key)
        
        if cached_data:
            return (cached_data['unidades_disponibles'], 
                   cached_data['alias_unidades'],
                   set(cached_data['camionetas']), 
                   set(cached_data['autos']))
        
        # Si no está en caché, generar y guardar
        with self._data_lock:
            unit_info = (
                self.UNIDADES_DISPONIBLES[:],
                self.ALIAS_UNIDADES.copy(),
                self.CAMIONETAS.copy(),
                self.AUTOS.copy()
            )
            
            # Guardar en caché
            cache_data = {
                'unidades_disponibles': unit_info[0],
                'alias_unidades': unit_info[1],
                'camionetas': list(unit_info[2]),
                'autos': list(unit_info[3])
            }
            self.cache.set(cache_key, cache_data)
            
            return unit_info

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
        """Valida campo KM con reglas mejoradas."""
        if not km or not km.strip():
            return ("⚠️ KM requerido", "orange")
        
        try:
            km_int = int(km)
            if km_int < 0:
                return ("❌ KM no puede ser negativo", "red")
            elif km_int > 999999:
                return ("❌ KM demasiado alto", "red")
            elif km_int == 0:
                return ("⚠️ Verificar KM = 0", "orange")
            else:
                return ("✅ KM válido", "green")
        except ValueError:
            return ("❌ KM debe ser numérico", "red")
    
    def _validar_ap(self, ap: str) -> Tuple[str, str]:
        """Valida campo Auxilio Público con reglas mejoradas."""
        if not ap or not ap.strip():
            return ("⚠️ AP requerido", "orange")
        
        try:
            ap_int = int(ap)
            if ap_int < 0:
                return ("❌ AP no puede ser negativo", "red")
            elif ap_int > 999999:
                return ("❌ AP demasiado alto", "red")
            elif ap_int == 0:
                return ("⚠️ Verificar AP = 0", "orange")
            else:
                return ("✅ AP válido", "green")
        except ValueError:
            return ("❌ AP debe ser numérico", "red")
    
    def _validar_po(self, po: str) -> Tuple[str, str]:
        """Valida campo Parte de Ocurrencias con reglas mejoradas."""
        if not po or not po.strip():
            return ("⚠️ PO requerido", "orange")
        
        try:
            po_int = int(po)
            if po_int < 0:
                return ("❌ PO no puede ser negativo", "red")
            elif po_int > 10:
                return ("❌ PO máximo 10", "red")
            else:
                return ("✅ PO válido", "green")
        except ValueError:
            return ("❌ PO debe ser numérico", "red")

    def guardar_registro(self, units_data: List[Dict], turno: str) -> bool:
        """Guarda registro con validación."""
        try:
            with self._data_lock:
                # Validar datos antes de guardar
                if not self._validate_units_data(units_data):
                    return False
                
                # Guardar en múltiples formatos para redundancia
                success_json = self._save_to_json(units_data, turno)
                success_excel = self._save_to_excel(units_data, turno)
                success_cache = self._save_to_cache(units_data, turno)
                
                # Consideramos éxito si al menos un formato funciona
                if success_json or success_excel or success_cache:
                    self._update_last_save_info(units_data, turno)
                    print(f"[MODELO] Registro guardado exitosamente")
                    return True
                else:
                    print(f"[ERROR] Falló guardado en todos los formatos")
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
    
    def _save_to_json(self, units_data: List[Dict], turno: str) -> bool:
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
    
    def _save_to_excel(self, units_data: List[Dict], turno: str) -> bool:
        """Guarda datos en archivo Excel con formato mejorado."""
        try:
            import openpyxl
            
            # Cargar o crear libro de trabajo
            if os.path.exists(self.EXCEL_BACKUP_FILE):
                workbook = openpyxl.load_workbook(self.EXCEL_BACKUP_FILE)
                worksheet = workbook.active
            else:
                self._initialize_excel_backup()
                workbook = openpyxl.load_workbook(self.EXCEL_BACKUP_FILE)
                worksheet = workbook.active
            
            # Encontrar la siguiente fila disponible
            next_row = worksheet.max_row + 1
            
            timestamp = datetime.now()
            fecha = timestamp.strftime("%d/%m/%Y")
            hora = timestamp.strftime("%H:%M:%S")
            
            # Agregar datos por cada unidad
            for unit in units_data:
                worksheet.cell(row=next_row, column=1, value=fecha)
                worksheet.cell(row=next_row, column=2, value=hora)
                worksheet.cell(row=next_row, column=3, value=turno)
                worksheet.cell(row=next_row, column=4, value=unit['alias'])
                worksheet.cell(row=next_row, column=5, value=unit['km'])
                worksheet.cell(row=next_row, column=6, value=unit['ap'])
                worksheet.cell(row=next_row, column=7, value=unit['po'])
                worksheet.cell(row=next_row, column=8, value=', '.join(unit.get('turnos_seleccionados', [])))
                
                # Calcular observaciones
                obs_km, obs_ap, obs_po = self.calcular_observaciones(unit['km'], unit['ap'], unit['po'])
                observaciones = f"KM: {obs_km[0]}, AP: {obs_ap[0]}, PO: {obs_po[0]}"
                worksheet.cell(row=next_row, column=9, value=observaciones)
                
                next_row += 1
            
            # Guardar archivo
            workbook.save(self.EXCEL_BACKUP_FILE)
            print(f"[MODELO] Guardado Excel: {self.EXCEL_BACKUP_FILE}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error guardando Excel: {e}")
            return False
    
    def _save_to_cache(self, units_data: List[Dict], turno: str) -> bool:
        """Guarda datos en caché para acceso rápido."""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'turno': turno,
                'units': units_data
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

    def cargar_ultimo_registro(self) -> Optional[Dict]:
        """Carga el último registro guardado."""
        try:
            # Intentar cargar desde caché primero
            last_record = self.cache.get("last_record")
            if last_record:
                print("[MODELO] Último registro cargado desde caché")
                return last_record
            
            # Si no hay en caché, intentar cargar desde archivos JSON
            json_dir = "data_json"
            if os.path.exists(json_dir):
                json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
                if json_files:
                    # Ordenar por fecha (más reciente primero)
                    json_files.sort(reverse=True)
                    latest_file = os.path.join(json_dir, json_files[0])
                    
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Guardar en caché para próximas consultas
                    self.cache.set("last_record", data, persist=True)
                    print(f"[MODELO] Último registro cargado desde archivo: {latest_file}")
                    return data
            
            print("[MODELO] No se encontraron registros anteriores")
            return None
            
        except Exception as e:
            print(f"[ERROR] Error cargando último registro: {e}")
            return None

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

    def agregar_unidad(self, alias: str, codigo: str, tipo: str) -> bool:
        """Agrega una nueva unidad al sistema."""
        try:
            with self._data_lock:
                # Usar el gestor de archivos para agregar
                if self.units_manager.add_unit(alias, codigo, tipo):
                    # Recargar datos
                    self._cargar_unidades_desde_archivo()
                    print(f"[MODELO] Unidad agregada exitosamente: {alias}")
                    return True
                else:
                    print(f"[ERROR] No se pudo agregar la unidad: {alias}")
                    return False
                    
        except Exception as e:
            print(f"[ERROR] Error agregando unidad: {e}")
            return False

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
            # Guardar configuración actual
            config_to_save = {
                'version': getattr(self, 'version', '2.0'),
                'last_update': datetime.now().isoformat(),
                'validation_rules': getattr(self, 'validation_rules', {})
            }
            self.cache.set("model_config", config_to_save, persist=True)
            
            # Cerrar caché
            self.cache.shutdown()
            
            print("[MODELO] Cerrado correctamente")
            
        except Exception as e:
            print(f"[ERROR] Error cerrando modelo: {e}")

# Alias para compatibilidad
Model = OptimizedModel