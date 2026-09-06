# model.py (versión optimizada)
import hashlib
import json
import locale
import math
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill  # Agrega PatternFill aquí
from openpyxl.utils import get_column_letter  # Agrega get_column_letter aquí
import os
import pickle
import sys
from datetime import datetime, timedelta
from cache import CacheManager

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


class Model:
    def __init__(self, cache_manager=None):
        # Configuración de caché
        self.cache = cache_manager or CacheManager()
        
        # Cargar configuración desde caché o inicializar
        self._load_or_initialize_config()
                        
        self.IMG_FOLDER = "IMG"
        self.LINK_GEOSATELITAL = "https://panel.geosatelital.com/dashboard"
        self.LINK_SIPCOP = "https://seguridadciudadana.mininter.gob.pe/sipcop-m/reportes/mapa-recorrido-vehiculo"
        
        # Cargar datos de unidades desde caché o inicializar
        self._load_or_initialize_units()
        
        # Configurar locale para fechas
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Linux
        except locale.Error:
            try:
                locale.setlocale(locale.LC_TIME, 'spanish')  # Windows
            except locale.Error:
                pass # Fallback si no se puede configurar el locale

        # Configurar archivo de respaldo Excel
        self.EXCEL_BACKUP_FILE = "unidades_registro.xlsx"
        self._initialize_excel_backup()

    def _initialize_excel_backup(self):
        """Inicializa el archivo Excel de respaldo con las columnas necesarias."""
        columns = [
            "🚓 UNIDADES", "🚔 KM", "📌 A.P", "📒 P.O", 
            "🕵️‍♂️ TURNO", "🌙 OBS-TURNO", "🕰️ HORA", "📅 FECHA"
        ]
        
        if not os.path.exists(self.EXCEL_BACKUP_FILE):
            df = pd.DataFrame(columns=columns)
            df.to_excel(self.EXCEL_BACKUP_FILE, index=False)
            self._format_excel_file()
    
    def _format_excel_file(self):
        """Aplica formato al archivo Excel para mejor legibilidad."""
        try:
            wb = load_workbook(self.EXCEL_BACKUP_FILE)
            ws = wb.active
            
            # Aplicar formato a los encabezados
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
            
            for cell in ws[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center")
            
            # Ajustar ancho de columnas
            column_widths = [20, 10, 10, 10, 15, 20, 15, 15]
            for i, width in enumerate(column_widths, start=1):
                ws.column_dimensions[get_column_letter(i)].width = width
                
            wb.save(self.EXCEL_BACKUP_FILE)
        except Exception as e:
            print(f"Error al formatear archivo Excel: {str(e)}")

    def _load_cache(self, key):
        """Carga datos del caché usando el CacheManager."""
        return self.cache.get(key)  
    
    def _save_cache(self, key, value, ttl=None):
        """Guarda datos en el caché usando el CacheManager."""
        return self.cache.set(key, value, ttl)      
        
    def _load_or_initialize_config(self):
        """Carga la configuración desde caché o inicializa valores por defecto."""
        cached_config = self._load_cache("db_config")
        if cached_config:
            self.DB_CONFIG = cached_config
        else:
            # Configuración por defecto
            self.DB_CONFIG = {
                'host': 'localhost',
                'database': 'serenazgo_db',
                'user': 'root',
                'password': '',
                'port': '3306'
            }
            self._save_cache("db_config", self.DB_CONFIG)

    def _load_or_initialize_units(self):
        """Carga los datos de unidades desde caché o inicializa valores por defecto."""
        cached_units = self._load_cache("units_data")
        if cached_units:
            self.CAMIONETAS = cached_units['camionetas']
            self.AUTOS = cached_units['autos']
            self.ALIAS_UNIDADES = cached_units['alias']
            self.UNIDADES_DISPONIBLES = cached_units['disponibles']
        else:
            # Configuración original de vehículos
            self.CAMIONETAS = {"EUI-621", "EUI-682", "EUI-683", "EUI-646", 
                              "EUI-685", "EUI-686", "EUI-679", "EUI-680"}
            self.AUTOS = {"EUI-645", "EUI-647", "EUI-668"}
            self.ALIAS_UNIDADES = {
                "H1 / EUI-621": "EUI-621", "H2 / EUI-682": "EUI-682", 
                "H3 / EUI-683": "EUI-683", "H4 / EUI-646": "EUI-646", 
                "H5 / EUI-685": "EUI-685", "H6 / EUI-686": "EUI-686",
                "H7 / EUI-679": "EUI-679", "H8 / EUI-680": "EUI-680", 
                "H9 / EUI-645": "EUI-645", "H10 / EUI-647": "EUI-647", 
                "H11 / EUI-668": "EUI-668"
            }
            self.UNIDADES_DISPONIBLES = list(self.ALIAS_UNIDADES.keys())
            
            # Guardar en caché
            self._save_cache("units_data", {
                'camionetas': self.CAMIONETAS,
                'autos': self.AUTOS,
                'alias': self.ALIAS_UNIDADES,
                'disponibles': self.UNIDADES_DISPONIBLES
            })

    

    def _get_db_connection(self):
        """Establece conexión con la base de datos MySQL."""
        try:
            print(f"Intentando conectar a MySQL con configuración: {self.DB_CONFIG}")  # Debug
            conn = mysql.connector.connect(**self.DB_CONFIG)
            print("Conexión exitosa a MySQL")  # Debug
            return conn
        except Error as e:
            print(f"Error al conectar a MySQL: {e}")  # Debug
            # Intentar crear la base de datos si no existe
            try:
                conn = mysql.connector.connect(
                    host=self.DB_CONFIG['host'],
                    user=self.DB_CONFIG['user'],
                    password=self.DB_CONFIG['password']
                )
                cursor = conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.DB_CONFIG['database']}")
                conn.close()
                
                # Reconectar con la base de datos creada
                conn = mysql.connector.connect(**self.DB_CONFIG)
                self._initialize_database(conn)
                return conn
            except Exception as e:
                print(f"Error al crear la base de datos: {e}")
                return None

    def _initialize_database(self, conn):
        """Inicializa la base de datos con las tablas necesarias."""
        cursor = conn.cursor()
        
        # Crear tabla tbl_kmappo si no existe
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_kmappo (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            ID_Unidad INT NOT NULL,
            KM INT,
            AP INT,
            PO INT,
            ID_Turno INT,
            obs_turno VARCHAR(50),
            hora_Registro TIME,
            fecha_Registro DATE
        )
        """)
        
        conn.commit()
        cursor.close()
    
    def obtener_ultimo_registro(self, force_fresh=False):
        """Obtiene el último registro con soporte para caché."""
        if not force_fresh:
            cached_data = self.cache.get("last_record")
            if cached_data:
                return cached_data
                
        # Si no hay caché o se fuerza actualización, consultar la BD
        conn = self._get_db_connection()
        if not conn:
            return None

        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
            SELECT fecha_Registro, hora_Registro 
            FROM tbl_kmappo 
            ORDER BY fecha_Registro DESC, hora_Registro DESC 
            LIMIT 1
            """
            cursor.execute(query)
            ultimo_registro = cursor.fetchone()
            
            if not ultimo_registro:
                return None
                
            query = """
            SELECT ID_Unidad, KM, AP, PO, ID_Turno, obs_turno 
            FROM tbl_kmappo 
            WHERE fecha_Registro = %s AND hora_Registro = %s
            ORDER BY ID_Unidad
            """
            cursor.execute(query, (ultimo_registro['fecha_Registro'], ultimo_registro['hora_Registro']))
            registros = cursor.fetchall()
            
            id_to_alias = {
                1: "H1 / EUI-621", 2: "H2 / EUI-682", 3: "H3 / EUI-683",
                4: "H4 / EUI-646", 5: "H5 / EUI-685", 6: "H6 / EUI-686",
                7: "H7 / EUI-679", 8: "H8 / EUI-680", 9: "H9 / EUI-645",
                10: "H10 / EUI-647", 11: "H11 / EUI-668"
            }
            
            id_to_turno = {1: "NOCHE", 2: "DÍA", 3: "TARDE"}
            
            resultado = []
            for registro in registros:
                alias = id_to_alias.get(registro['ID_Unidad'], f"ID_{registro['ID_Unidad']}")
                turno_principal = id_to_turno.get(registro['ID_Turno'], "DESCONOCIDO")
                turnos = registro['obs_turno'].split('-') if registro['obs_turno'] else []
                
                resultado.append({
                    'alias': alias,
                    'km': str(registro['KM']),
                    'ap': str(registro['AP']),
                    'po': str(registro['PO']),
                    'turno_principal': turno_principal,
                    'turnos_seleccionados': turnos
                })
            
            # Guardar en caché antes de retornar
            if resultado:
                self.cache.set("last_record", resultado)
            return resultado
            
        except Error as e:
            print(f"Error al consultar último registro: {str(e)}")
            return None
        finally:
            if cursor:
                cursor.close()
            conn.close()

    def guardar_datos_mysql(self, unidades_data, turno_principal):
        """Guarda los datos en la base de datos MySQL con respaldo en Excel."""
        # Primero intentar guardar en MySQL
        success_mysql, msg_mysql = self._guardar_en_mysql(unidades_data, turno_principal)
        
        # Si falla MySQL, guardar en Excel
        if not success_mysql:
            success_excel, msg_excel = self._guardar_en_excel(unidades_data, turno_principal)
            return success_excel, f"MySQL: {msg_mysql}\nExcel: {msg_excel}"
        
        # Si MySQL tiene éxito, también guardar en Excel como respaldo
        self._guardar_en_excel(unidades_data, turno_principal)
        return success_mysql, msg_mysql

    def _guardar_en_mysql(self, unidades_data, turno_principal):
        """Método privado para guardar en MySQL (código existente)."""
        conn = self._get_db_connection()
        if not conn:
            error_msg = "No se pudo establecer conexión con la base de datos"
            print(error_msg)  # Debug
            return False, error_msg
            
        cursor = None
        try:
            cursor = conn.cursor()
            
            # Mapeo de turnos a IDs (deberías tener una tabla de turnos en la BD)
            turno_ids = {'NOCHE': 1, 'DÍA': 2, 'TARDE': 3}
            turno_id = turno_ids.get(turno_principal, 0)
            
            # Mapeo de unidades a IDs (deberías tener una tabla de unidades en la BD)
            unidad_ids = {
                'EUI-621': 1, 'EUI-682': 2, 'EUI-683': 3, 'EUI-646': 4,
                'EUI-685': 5, 'EUI-686': 6, 'EUI-679': 7, 'EUI-680': 8,
                'EUI-645': 9, 'EUI-647': 10, 'EUI-668': 11
            }
            
            ahora = datetime.now()  # <-- Usar datetime local directamente
            fecha = ahora.strftime('%Y-%m-%d')
            hora = ahora.strftime('%H:%M:%S')
            
            for data in unidades_data:
                unidad_real = self.ALIAS_UNIDADES.get(data['alias'], data['alias'])
                unidad_id = unidad_ids.get(unidad_real, 0)
                
                if not unidad_id:
                    continue
                
                # Convertir valores a enteros
                try:
                    km = int(data['km']) if data['km'] else 0
                    ap = int(data['ap']) if data['ap'] else 0
                    po = int(data['po']) if data['po'] else 0
                except ValueError:
                    continue
                
                obs_turno = '-'.join(data['turnos_seleccionados']) if data['turnos_seleccionados'] else ''
                
                query = """
                INSERT INTO tbl_kmappo 
                (ID_Unidad, KM, AP, PO, ID_Turno, obs_turno, hora_Registro, fecha_Registro)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (unidad_id, km, ap, po, turno_id, obs_turno, hora, fecha)
                
                cursor.execute(query, params)
            
            conn.commit()
            return True, "Datos guardados correctamente en MySQL"
            
        except Error as e:
            error_msg = f"Error al guardar en MySQL: {str(e)}"
            print(error_msg)  # Debug
            if conn:
                conn.rollback()
            return False, error_msg
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def _guardar_en_excel(self, unidades_data, turno_principal):
        """Guarda los datos en el archivo Excel de respaldo."""
        try:
            ahora = datetime.now()
            fecha = ahora.strftime('%Y-%m-%d')
            hora = ahora.strftime('%H:%M:%S')
            
            # Preparar datos para Excel
            excel_data = []
            for data in unidades_data:
                unidad_real = self.ALIAS_UNIDADES.get(data['alias'], data['alias'])
                obs_turno = '-'.join(data['turnos_seleccionados']) if data['turnos_seleccionados'] else ''
                
                excel_data.append([
                    data['alias'],         # 🚓 UNIDADES
                    data['km'],            # 🚔 KM
                    data['ap'],           # 📌 A.P
                    data['po'],           # 📒 P.O
                    turno_principal,      # 🕵️‍♂️ TURNO
                    obs_turno,             # 🌙 OBS-TURNO
                    hora,                  # 🕰️ HORA
                    fecha                  # 📅 FECHA
                ])
            
            # Leer archivo existente y agregar nuevos datos
            df_existing = pd.read_excel(self.EXCEL_BACKUP_FILE)
            df_new = pd.DataFrame(excel_data, columns=df_existing.columns)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            
            # Guardar y formatear
            df_combined.to_excel(self.EXCEL_BACKUP_FILE, index=False)
            self._format_excel_file()
            
            return True, "Datos guardados correctamente en Excel"
            
        except Exception as e:
            error_msg = f"Error al guardar en Excel: {str(e)}"
            print(error_msg)
            return False, error_msg

    def validar_entrada(self, valor):
        """
        Valida que la entrada sea un número o esté vacía.
        """
        return valor == "" or valor.isdigit()

    def calcular_observaciones(self, km_text, ap_text, po_text):
        """
        Calcula las observaciones de KM, AP y PO basadas en los valores de entrada.
        Retorna tuplas (texto, color_texto, color_fondo, fuente) para cada observación.
        """
        default_obs = ("---", "black", "#F0F0F0", ("Helvetica", 10))

        if not km_text or not ap_text or not po_text:
            return default_obs, default_obs, default_obs

        try:
            km = int(km_text)
            ap = int(ap_text)
            po = int(po_text)

            if km < 0 or ap < 0 or po < 0:
                raise ValueError("Valores no pueden ser negativos")

            obs_km = ("✅ COMPLETO", "black", "lightgreen", ("Helvetica", 10, "bold")) if km >= 90 else \
                     (f"❎ FALTA {90 - km} KM", "white", "tomato", ("Helvetica", 10, "bold"))

            faltante_ap = 230 - ap
            tacticos = math.ceil(faltante_ap / 30) if faltante_ap > 0 else 0
            obs_ap = ("✅ COMPLETO (8T)", "black", "lightgreen", ("Helvetica", 10, "bold")) if ap >= 230 else \
                     (f"❎ FALTA {faltante_ap} MIN ({tacticos}T)", "white", "tomato", ("Helvetica", 10, "bold"))

            obs_po = ("✅ COMPLETO", "black", "lightgreen", ("Helvetica", 10, "bold")) if po >= 3 else \
                     (f"❎ FALTA {3 - po} PARTE{'S' if (3 - po) > 1 else ''}", "white", "tomato", ("Helvetica", 10, "bold"))

            return obs_km, obs_ap, obs_po

        except ValueError:
            return ("ERROR", "red", "#F0F0F0", ("Helvetica", 10)), \
                   ("ERROR", "red", "#F0F0F0", ("Helvetica", 10)), \
                   ("ERROR", "red", "#F0F0F0", ("Helvetica", 10))
     
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
            logo_path = os.path.join("REPORT", "serenazgo_logo.png")
            if os.path.exists(logo_path):
                try:
                    logo = Image.open(logo_path)
                    # Redimensionar logo (20% del ancho de la página)
                    logo_width = int(width * 0.2)
                    logo_height = int((logo.size[1] / logo.size[0]) * logo_width)
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
            x_position = margin + (logo_width if os.path.exists(logo_path) else 0) + 100
            
            # Título principal - TALARA (a la derecha del logo)
            title_text = "TALARA"
            draw.text((x_position, y_position), title_text, 
                     fill=blue_color, font=font_title)
            y_position += 120
            
            # Fecha (debajo del título)
            date_text = f"- {fecha_formateada} -"
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
            # Mover la definición de col_widths aquí para que sea accesible en ambas secciones
            col_widths = [250, 350, 250, 250, 250, width - (2*margin) - 1350]  # Ajuste preciso
            # Separar camionetas y autos
            camionetas_data = []
            autos_data = []
            for data in unidades_info:
                unidad_real = self.ALIAS_UNIDADES.get(data['alias'], data['alias'])
                if unidad_real in self.CAMIONETAS:
                    camionetas_data.append(data)
                elif unidad_real in self.AUTOS:
                    autos_data.append(data)
            
            # Función auxiliar para obtener alias "H"
            def get_h_alias(real_unit):
                for alias, unit in self.ALIAS_UNIDADES.items():
                    if unit == real_unit:
                        return alias.split(' / ')[0]
                return real_unit
            
            # --- TABLA CAMIONETAS ---
            if camionetas_data:
                # Encabezado de sección (centrado)
                section_title = "CAMIONETAS PICK-UP"
                text_width = draw.textlength(section_title, font=font_header)
                draw.text(((width - text_width) // 2, y_position), section_title, 
                         fill=blue_color, font=font_header)
                y_position += 120
                
                # Encabezados de tabla
                headers = ["UNIDAD", "PLACA", "KM", "AP", "PO", "OBS"]
                                
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
                    h_alias = get_h_alias(unidad_real)
                    
                    # Color de fila alternado (azul claro/blanco)
                    fill_color = (230, 240, 255) if i % 2 == 0 else (255, 255, 255)
                    draw.rectangle([(margin, y_position), (width-margin, y_position+90)], fill=fill_color)
                    
                    # Dibujar bordes de celda
                    draw.rectangle([(margin, y_position), (width-margin, y_position+90)], outline=(200, 200, 200), width=2)
                    
                    x_pos = margin
                    # UNIDAD
                    draw.text((x_pos + col_widths[0]//2, y_position+45), h_alias, 
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[0], y_position), (x_pos+col_widths[0], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[0]
                    
                    # PLACA
                    draw.text((x_pos + col_widths[1]//2, y_position+45), unidad_real, 
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[1], y_position), (x_pos+col_widths[1], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[1]
                    
                    # KM
                    km = str(data['km']) if data['km'] else "---"
                    draw.text((x_pos + col_widths[2]//2, y_position+45), km, 
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[2], y_position), (x_pos+col_widths[2], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[2]
                    
                    # AP
                    ap = str(data['ap']) if data['ap'] else "---"
                    draw.text((x_pos + col_widths[3]//2, y_position+45), ap, 
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[3], y_position), (x_pos+col_widths[3], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[3]
                    
                    # PO (con fondo amarillo)
                    po = str(data['po']) if data['po'] else "---"
                    draw.rectangle([(x_pos, y_position), (x_pos+col_widths[4], y_position+90)], fill=(255, 255, 153))
                    draw.text((x_pos + col_widths[4]//2, y_position+45), po, 
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[4], y_position), (x_pos+col_widths[4], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[4]
                    
                    # OBS
                    obs = ', '.join(data['turnos_seleccionados']) if data['turnos_seleccionados'] else "---"
                    draw.text((x_pos + 30, y_position+45), obs, 
                             fill=(0, 0, 0), font=font_table_content, anchor="lm")
                    
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
                headers = ["UNIDAD", "PLACA", "KM", "AP", "PO", "OBS"]
                
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
                    h_alias = get_h_alias(unidad_real)
                    
                    # Color de fila alternado (naranja claro/blanco)
                    fill_color = (255, 230, 204) if i % 2 == 0 else (255, 255, 255)
                    draw.rectangle([(margin, y_position), (width-margin, y_position+90)], fill=fill_color)
                    
                    # Dibujar bordes de celda
                    draw.rectangle([(margin, y_position), (width-margin, y_position+90)], outline=(200, 200, 200), width=2)
                    
                    x_pos = margin
                    # UNIDAD
                    draw.text((x_pos + col_widths[0]//2, y_position+45), h_alias, 
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[0], y_position), (x_pos+col_widths[0], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[0]
                    
                    # PLACA
                    draw.text((x_pos + col_widths[1]//2, y_position+45), unidad_real, 
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[1], y_position), (x_pos+col_widths[1], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[1]
                    
                    # KM
                    km = str(data['km']) if data['km'] else "---"
                    draw.text((x_pos + col_widths[2]//2, y_position+45), km, 
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[2], y_position), (x_pos+col_widths[2], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[2]
                    
                    # AP
                    ap = str(data['ap']) if data['ap'] else "---"
                    draw.text((x_pos + col_widths[3]//2, y_position+45), ap, 
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[3], y_position), (x_pos+col_widths[3], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[3]
                    
                    # PO (con fondo amarillo)
                    po = str(data['po']) if data['po'] else "---"
                    draw.rectangle([(x_pos, y_position), (x_pos+col_widths[4], y_position+90)], fill=(255, 255, 153))
                    draw.text((x_pos + col_widths[4]//2, y_position+45), po, 
                             fill=(0, 0, 0), font=font_table_content, anchor="mm")
                    draw.line([(x_pos+col_widths[4], y_position), (x_pos+col_widths[4], y_position+90)], 
                             fill=(200, 200, 200), width=2)
                    x_pos += col_widths[4]
                    
                    # OBS
                    obs = ', '.join(data['turnos_seleccionados']) if data['turnos_seleccionados'] else "---"
                    draw.text((x_pos + 30, y_position+45), obs, 
                             fill=(0, 0, 0), font=font_table_content, anchor="lm")
                    
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

    def get_links(self):
        return self.LINK_GEOSATELITAL, self.LINK_SIPCOP

    def get_unit_info(self):
        return self.UNIDADES_DISPONIBLES, self.ALIAS_UNIDADES, self.CAMIONETAS, self.AUTOS

    def get_excel_file_path(self):
        return self.EXCEL_FILE

    def get_img_folder(self):
        return self.IMG_FOLDER