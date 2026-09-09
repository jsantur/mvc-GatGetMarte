import requests
import json
import math
import logging
import re
import time
from datetime import datetime, timezone, timedelta


def _haversine(lat1, lon1, lat2, lon2):
    """Calcula distancia en km entre dos coordenadas GPS (fórmula haversine)."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _get_jurisdiction(lat, lon):
    """
    Determina la jurisdicción según la longitud:
    - Longitud >= -81.266 (Este): T.ALTA
    - Longitud < -81.266 (Oeste): SECTORIAL
    """
    if lon is None:
        return "SECTORIAL"
    return "T.ALTA" if lon >= -81.266 else "SECTORIAL"


class WialonAPI:
    BASE_URL = "https://hst-api.wialon.com/wialon/ajax.html"

    # Zona horaria de Perú (UTC-5)
    TIMEZONE_OFFSET = -5

    # Velocidad mínima en km/h para considerar que el vehículo está en movimiento
    MIN_SPEED_KMH = 3

    def __init__(self, token):
        self.token = token
        self.sid = None
        self.real_base_url = self.BASE_URL
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)

    def login(self):
        """Inicia sesión en Wialon usando el token. Actualiza la URL real del servidor."""
        params = {
            "svc": "token/login",
            "params": json.dumps({"token": self.token})
        }
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=15)
            data = response.json()
            if "eid" in data:
                self.sid = data["eid"]
                # CRÍTICO: usar la base_url que devuelve el servidor (puede ser .us en vez de .com)
                server_base = data.get("base_url", "").rstrip("/")
                if server_base:
                    self.real_base_url = server_base + "/wialon/ajax.html"
                return True
            else:
                self.logger.error(f"Error de login Wialon: {data}")
                return False
        except Exception as e:
            self.logger.error(f"Error de conexión Wialon: {e}")
            return False

    def logout(self):
        """Cierra la sesión activa en Wialon y limpia la conexión."""
        if self.sid and self.real_base_url:
            try:
                params = {"svc": "core/logout", "params": "{}", "sid": self.sid}
                self.session.get(self.real_base_url, params=params, timeout=5)
            except Exception:
                pass
        self.sid = None
        try:
            self.session.close()
        except Exception:
            pass

    def _get_all_units(self):
        """Obtiene el listado completo de unidades con su ID y nombre."""
        params = {
            "svc": "core/search_items",
            "params": json.dumps({
                "spec": {
                    "itemsType": "avl_unit",
                    "propName": "sys_name",
                    "propValueMask": "*",
                    "sortType": "sys_name"
                },
                "force": 1,
                "flags": 1,   # solo info básica (nombre + id)
                "from": 0,
                "to": 0
            }),
            "sid": self.sid
        }
        response = self.session.get(self.real_base_url, params=params, timeout=15)
        return response.json().get("items", [])

    def _load_day_messages(self, unit_id, timezone_offset=None):
        """
        Carga todos los mensajes GPS de la unidad para HOY (00:00 – 23:59 hora local).
        Retorna la lista de mensajes.
        """
        tz_offset = timezone_offset if timezone_offset is not None else self.TIMEZONE_OFFSET
        tz = timezone(timedelta(hours=tz_offset))
        now = datetime.now(tz)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=0)

        params = {
            "svc": "messages/load_interval",
            "params": json.dumps({
                "itemId": unit_id,
                "timeFrom": int(start.timestamp()),
                "timeTo": int(end.timestamp()),
                "flags": 0x0001,       # Mensajes con posición GPS
                "flagsMask": 0x0000,
                "loadCount": 0xFFFFFFFF
            }),
            "sid": self.sid
        }
        response = self.session.get(self.real_base_url, params=params, timeout=30)
        return response.json().get("messages", [])

    def _calc_km_from_messages(self, messages):
        """
        Calcula el kilometraje recorrido a partir de mensajes GPS usando haversine.
        Solo se suman segmentos donde el vehículo iba a >= MIN_SPEED_KMH.
        Se descartan saltos GPS absurdos (> 1 km entre mensajes consecutivos).
        """
        total_km = 0.0
        prev_lat = None
        prev_lon = None

        for msg in messages:
            pos = msg.get("pos")
            if not pos:
                continue

            lat = pos.get("y")
            lon = pos.get("x")
            spd = pos.get("s", 0)   # velocidad en km/h

            if lat is None or lon is None:
                continue

            if prev_lat is not None and spd >= self.MIN_SPEED_KMH:
                dist = _haversine(prev_lat, prev_lon, lat, lon)
                if dist < 1.0:   # descartar saltos GPS (> 1 km) por ruido
                    total_km += dist

            prev_lat, prev_lon = lat, lon

        return round(total_km, 2)

    # ------------------------------------------------------------------
    # MÉTODO PRINCIPAL: kilometraje recorrido HOY por intervalo (00:00-23:59)
    # ------------------------------------------------------------------
    def get_daily_mileage(self, wialon_names, timezone_offset=None):
        """
        Retorna el kilometraje RECORRIDO HOY para cada unidad.
        Usa el intervalo 00:00 – 23:59 (hora local Peru UTC-5).

        Args:
            wialon_names: lista de nombres de unidad tal como aparecen en Wialon.
            timezone_offset: offset horario (default -5 para Peru).

        Returns:
        Returns:
            dict {nombre_wialon: {"km": km_hoy, "jurisdiccion": juris}}
        """
        if not self.sid and not self.login():
            return {}

        normalize = lambda s: " ".join(s.split()).upper()
        norm_targets = {normalize(n): n for n in wialon_names}

        # Mapeo por placa para tolerancia total (ej. EUI-621)
        plate_targets = {}
        for n in wialon_names:
            m = re.search(r'(EUI-\d+)', n)
            if m:
                plate_targets[m.group(1).upper()] = n

        debug_info = []

        try:
            all_units = self._get_all_units()
            debug_info.append(f"URL: {self.real_base_url}")
            debug_info.append(f"Unidades en Wialon: {len(all_units)}")

            # Emparejar unidades objetivo
            matched_units = []
            for item in all_units:
                name = item.get("nm", "")
                norm_name = normalize(name)
                unit_id = item.get("id")

                orig_name = None
                if norm_name in norm_targets:
                    orig_name = norm_targets[norm_name]
                else:
                    m = re.search(r'(EUI-\d+)', name)
                    if m and m.group(1).upper() in plate_targets:
                        orig_name = plate_targets[m.group(1).upper()]

                if orig_name and unit_id:
                    matched_units.append((item, orig_name, unit_id))

            mileage_data = {}

            def _procesar_unidad(unit_data):
                item, orig_name, unit_id = unit_data
                name = item.get("nm", "")
                unit_logs = [f"\n--- {name} (ID: {unit_id}) ---"]
                try:
                    messages = self._load_day_messages(unit_id, timezone_offset)
                    unit_logs.append(f"  Mensajes GPS hoy: {len(messages)}")

                    if not messages:
                        unit_logs.append("  ⚠️ Sin mensajes para hoy")
                        return orig_name, {"km": 0.0, "jurisdiccion": "SECTORIAL", "last_lat": None, "last_lon": None}, unit_logs

                    km_hoy = self._calc_km_from_messages(messages)

                    # Obtener última posición para jurisdicción
                    juris = "SECTORIAL"
                    last_lat = None
                    last_lon = None
                    pos = item.get("pos")
                    if pos:
                        last_lat = pos.get("y")
                        last_lon = pos.get("x")
                    else:
                        last_valid_msg = next((m for m in reversed(messages) if m.get("pos")), None)
                        if last_valid_msg:
                            pos = last_valid_msg.get("pos")
                            last_lat = pos.get("y")
                            last_lon = pos.get("x")
                    
                    if last_lat is not None and last_lon is not None:
                        juris = _get_jurisdiction(last_lat, last_lon)
                        unit_logs.append(f"  📍 Última Pos: {last_lat}, {last_lon} -> {juris}")

                    unit_logs.append(f"  ✅ KM hoy: {km_hoy} | Juris: {juris}")
                    return orig_name, {"km": km_hoy, "jurisdiccion": juris, "last_lat": last_lat, "last_lon": last_lon}, unit_logs

                except Exception as e:
                    unit_logs.append(f"  ❌ Error calculando KM: {e}")
                    return orig_name, {"km": 0.0, "jurisdiccion": "SECTORIAL"}, unit_logs

            # Procesar unidades en paralelo para respuesta inmediata en tiempo real
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=5) as executor:
                results = executor.map(_procesar_unidad, matched_units)
                for orig_name, res_info, unit_logs in results:
                    mileage_data[orig_name] = res_info
                    debug_info.extend(unit_logs)

            # Guardar log de diagnóstico
            try:
                tz = timezone(timedelta(hours=self.TIMEZONE_OFFSET if timezone_offset is None else timezone_offset))
                hoy = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
                with open("wialon_debug.log", "w", encoding="utf-8") as f:
                    f.write(f"Consulta: {hoy}\n")
                    f.write("\n".join(debug_info))
            except Exception:
                pass

            # Guardar JSON crudo de la última búsqueda de unidades
            try:
                with open("wialon_raw_search.json", "w", encoding="utf-8") as f:
                    json.dump(all_units, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

            return mileage_data

        except Exception as e:
            self.logger.error(f"Error en get_daily_mileage: {e}")
            try:
                with open("wialon_error.log", "w", encoding="utf-8") as f:
                    f.write(f"Error: {str(e)}\nURL: {self.real_base_url}\nSID: {self.sid}")
            except Exception:
                pass
            return {}

    # ------------------------------------------------------------------
    # LEGADO: kilometraje total del odómetro (ya no es el método principal)
    # ------------------------------------------------------------------
    def get_unit_mileage(self, wialon_names):
        """
        [LEGADO] Retorna el odómetro total acumulado de cada unidad.
        Para el recorrido diario usa get_daily_mileage().
        """
        if not self.sid and not self.login():
            return {}

        normalize = lambda s: " ".join(s.split()).upper()
        norm_targets = {normalize(name): name for name in wialon_names}

        params = {
            "svc": "core/search_items",
            "params": json.dumps({
                "spec": {
                    "itemsType": "avl_unit",
                    "propName": "sys_name",
                    "propValueMask": "*",
                    "sortType": "sys_name"
                },
                "force": 1,
                "flags": 1 | 256 | 1024 | 4096 | 8192,
                "from": 0,
                "to": 0
            }),
            "sid": self.sid
        }

        try:
            results = requests.get(self.real_base_url, params=params, timeout=15).json()
            mileage_data = {}
            for item in results.get("items", []):
                name = item.get("nm", "")
                norm = normalize(name)
                if norm not in norm_targets:
                    continue
                orig = norm_targets[norm]
                cnm = item.get("cnm")
                if cnm is not None and cnm > 0:
                    mileage_data[orig] = round(float(cnm), 2)
            return mileage_data
        except Exception as e:
            self.logger.error(f"Error get_unit_mileage: {e}")
            return {}

    # ------------------------------------------------------------------
    # REPORTES: A.P. desde Cronologías de Estacionamiento
    # ------------------------------------------------------------------

    # IDs conocidos del recurso y plantilla (descubiertos vía test)
    REPORT_RESOURCE_ID = 402190383       # Recurso "SERENAZGO TALARA"
    REPORT_TEMPLATE_ID = 5              # "INFORME DE PRODUCCION DIARIO"
    AP_DISCOUNT_MINUTES = 0             # ❌ DESCUENTO ELIMINADO (pedido usuario)
    AP_ROUND_BLOCK_MINUTES = 5          # Redondeo INDIVIDUAL por evento a bloques de 5 min
    AP_MIN_EVENT_SECONDS = 31           # Solo eventos con duración > 31s se incluyen (≅0.30 min)

    # ==================================================================
    # GEOCERCAS PERMITIDAS PARA CÁLCULO DE A.P.
    # 4 rectángulos grandes que cubren NORTE / CENTRO / SUR / ENACE
    # en Talara. Orden de coordenadas (lat, lon):
    #   lat más negativa = SUR ; lon más negativa = OESTE
    # ==================================================================
    ALLOWED_GEOFENCES = [
        # ────────────────── ZONA NORTE ──────────────────
        # Desde límite norte (~-4.550) hasta Av. Bolognesi (~-4.575).
        # Límite ESTE hasta -81.1970 (frontera oeste de ENACE) para
        # cubrir sin huecos: Posta Médica, Milla 7, Panamericana N.
        {"name": "NORTE", "zone": "NORTE", "polygon": [
            (-4.5500, -81.2950),
            (-4.5500, -81.1970),
            (-4.5750, -81.1970),
            (-4.5750, -81.2950),
            (-4.5500, -81.2950),
        ]},
        # ────────────────── ZONA CENTRO ──────────────────
        # Entre Av. Bolognesi (~-4.575) y ~-4.588.
        # Cubre: Plaza Grau, mercado, Av. F, Av. H, Av. G,
        #        Av. Miguel Grau, Av. Postigo, Av. Castilla,
        #        Milla 7, Posta Médica (hasta frontera ENACE).
        {"name": "CENTRO", "zone": "CENTRO", "polygon": [
            (-4.5750, -81.2900),
            (-4.5750, -81.1970),
            (-4.5880, -81.1970),
            (-4.5880, -81.2900),
            (-4.5750, -81.2900),
        ]},
        # ────────────────── ZONA SUR ──────────────────
        # Desde ~-4.588 hacia el sur.
        # Cubre: Negreiros, Nueva Talara, San Sebastián, Villa Talara,
        #        y franja este hasta límite de ENACE.
        {"name": "SUR", "zone": "SUR", "polygon": [
            (-4.5880, -81.2820),
            (-4.5880, -81.1970),
            (-4.6050, -81.1970),
            (-4.6050, -81.2820),
            (-4.5880, -81.2820),
        ]},
        # ────────────────── ZONA ENACE ──────────────────
        # Talara Alta / Enace / Alan García / Urb. Enace, etc.
        {"name": "ENACE", "zone": "ENACE", "polygon": [
            (-4.5750, -81.1970),
            (-4.5750, -81.1690),
            (-4.6030, -81.1690),
            (-4.6030, -81.1970),
            (-4.5750, -81.1970),
        ]},
    ]

    # ──────────────────────────────────────────────────────────────────
    # ALGORITMO POINT-IN-POLYGON (Ray Casting)
    # ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _point_in_polygon(lat, lon, polygon):
        """
        Determina si un punto (lat, lon) está dentro de un polígono
        usando el algoritmo de Ray-Casting (even-odd rule).

        Args:
            lat: latitud del punto (y)
            lon: longitud del punto (x)
            polygon: lista de tuplas [(lat, lon), ...] cerrada

        Returns:
            True si el punto está dentro o en el borde.
        """
        if lat is None or lon is None or not polygon:
            return False

        n = len(polygon)
        inside = False

        j = n - 1
        for i in range(n):
            xi, yi = polygon[i][1], polygon[i][0]   # lon = x, lat = y
            xj, yj = polygon[j][1], polygon[j][0]

            # Comprobar si el borde cruza el rayo horizontal del punto
            if ((yi > lat) != (yj > lat)):
                # Calcular intersección x entre el borde y el rayo
                x_intersect = (xj - xi) * (lat - yi) / (yj - yi) + xi
                if lon <= x_intersect:
                    inside = not inside
            j = i

        return inside

    def _is_inside_allowed_geofence(self, lat, lon):
        """
        Verifica si (lat, lon) pertenece a ALGUNA de las geocercas permitidas
        (NORTE, CENTRO, SUR, ENACE).

        Returns:
            tuple (esta_dentro: bool, nombre_zona: str|None, nombre_geocerca: str|None)
        """
        for gf in self.ALLOWED_GEOFENCES:
            if self._point_in_polygon(lat, lon, gf["polygon"]):
                return True, gf["zone"], gf["name"]
        return False, None, None

    def _find_report_template(self, template_name="INFORME DE PRODUCCION DIARIO"):
        """
        Busca el reportResourceId y reportTemplateId de una plantilla.
        Retorna (resource_id, template_id) o (None, None) si no se encuentra.
        """
        params = {
            "svc": "core/search_items",
            "params": json.dumps({
                "spec": {
                    "itemsType": "avl_resource",
                    "propName": "sys_name",
                    "propValueMask": "*",
                    "sortType": "sys_name"
                },
                "force": 1,
                "flags": 0x2000 | 1,
                "from": 0,
                "to": 0
            }),
            "sid": self.sid
        }
        response = requests.get(self.real_base_url, params=params, timeout=15)
        resources = response.json()

        for item in resources.get("items", []):
            templates = item.get("rep", {})
            for tid, tdata in templates.items():
                if tdata.get("n", "").upper() == template_name.upper():
                    return item["id"], int(tid)
        return None, None

    def _cleanup_report(self):
        """Limpia resultados de reportes anteriores en la sesión."""
        requests.get(self.real_base_url, params={
            "svc": "report/cleanup_result",
            "params": "{}",
            "sid": self.sid
        }, timeout=10)

    def _exec_report(self, resource_id, template_id, unit_id, time_from, time_to):
        """
        Ejecuta un reporte y retorna el resultado completo.
        """
        params = {
            "svc": "report/exec_report",
            "params": json.dumps({
                "reportResourceId": resource_id,
                "reportTemplateId": template_id,
                "reportObjectId": unit_id,
                "reportObjectSecId": 0,
                "interval": {
                    "from": time_from,
                    "to": time_to,
                    "flags": 0
                }
            }),
            "sid": self.sid
        }
        response = requests.get(self.real_base_url, params=params, timeout=30)
        return response.json()

    @staticmethod
    def _parse_duration_to_minutes(duration_str):
        """Convierte duración 'HH:MM:SS' o 'H:MM:SS' a minutos (float)."""
        if not duration_str or ":" not in str(duration_str):
            return 0.0
        parts = str(duration_str).split(":")
        try:
            if len(parts) == 3:
                h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
                return h * 60 + m + s / 60.0
            elif len(parts) == 2:
                m, s = int(parts[0]), int(parts[1])
                return m + s / 60.0
        except ValueError:
            return 0.0
        return 0.0

    @staticmethod
    def _parse_duration_to_seconds(duration_str):
        """Convierte duración 'HH:MM:SS' a SEGUNDOS totales (int). Usado para filtro >31s."""
        if not duration_str or ":" not in str(duration_str):
            return 0
        parts = str(duration_str).split(":")
        try:
            if len(parts) == 3:
                h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
                return h * 3600 + m * 60 + s
            elif len(parts) == 2:
                m, s = int(parts[0]), int(parts[1])
                return m * 60 + s
        except ValueError:
            return 0
        return 0

    def _get_parking_minutes_from_report(self, chrono_table_idx, tables):
        """
        Extrae la duración de eventos de ESTACIONAMIENTO desde la tabla de
        cronologías (soporta inglés "Parking" y español "Estacionamiento").

        Navega: Nivel1 (día) → Nivel2 (Estacionamiento / Detención / Viaje).

        Para CADA evento extrae sus coordenadas iniciales (si están disponibles
        en la celda) y verifica si están dentro de las geocercas NORTE / CENTRO
        / SUR / ENACE.

        FALLBACK CRÍTICO: si NO se pueden extraer coordenadas GPS del evento,
        se INCLUYE el minuto de todos modos (para no perder total). El usuario
        debe importar los polígonos reales para precisión total.

        Returns:
            tupla (total_parking_min, eventos, zonas, total_sin_filtro)
        """
        table_info = tables[chrono_table_idx]
        top_rows = table_info.get("rows", 0)

        if top_rows == 0:
            return 0.0, [], {}, 0.0

        resp = requests.get(self.real_base_url, params={
            "svc": "report/get_result_rows",
            "params": json.dumps({
                "tableIndex": chrono_table_idx,
                "indexFrom": 0,
                "indexTo": top_rows - 1
            }),
            "sid": self.sid
        }, timeout=15)
        rows_l1 = resp.json()

        total_parking_min = 0.0
        total_sin_filtro = 0.0
        eventos_detalle = []
        zonas_acumulado = {}
        raw_guardado = False

        for i, _ in enumerate(rows_l1):
            resp2 = requests.get(self.real_base_url, params={
                "svc": "report/get_result_subrows",
                "params": json.dumps({
                    "tableIndex": chrono_table_idx,
                    "rowIndex": i
                }),
                "sid": self.sid
            }, timeout=15)
            subrows = resp2.json()

            # ── Guardar el primer batch de subrows para DEBUG (1 sola vez)
            if not raw_guardado and isinstance(subrows, list) and len(subrows) > 0:
                try:
                    with open("wialon_subrows_raw.json", "w", encoding="utf-8") as f:
                        json.dump(subrows[:3], f, ensure_ascii=False, indent=2)
                    raw_guardado = True
                except Exception:
                    pass

            if not isinstance(subrows, list):
                continue

            for sub in subrows:
                cells = sub.get("c", [])
                cell_vals = [c.get("t", "") if isinstance(c, dict) else str(c) for c in cells]
                tipo = cell_vals[1] if len(cell_vals) > 1 else ""

                # ═══════════════════════════════════════════════════════════
                # ✅ FIX PRINCIPAL: detectar "Estacionamiento" en español
                #    y también variantes como Parking / Stop / Detención
                # ═══════════════════════════════════════════════════════════
                tipo_lower = tipo.lower().strip()
                es_estacionamiento = (
                    "parking" in tipo_lower
                    or "estacionam" in tipo_lower   # estacionamiento, estacionados
                    or "estaciona" in tipo_lower
                    or "deten" in tipo_lower        # detención, detenido
                    or tipo_lower == "stop"
                )

                if not es_estacionamiento:
                    continue

                # ═══════════════════════════════════════════════════════════
                # ✅ EXPANDIR EVENTOS INDIVIDUALES (NIVEL 3 "r")
                # Si sub contiene "r" (lista de sub-eventos de estacionamiento),
                # procesar CADA evento por separado. De lo contrario, usar sub.
                # ═══════════════════════════════════════════════════════════
                items_to_process = sub.get("r", [])
                if not isinstance(items_to_process, list) or len(items_to_process) == 0:
                    items_to_process = [sub]

                for item in items_to_process:
                    item_cells = item.get("c", [])
                    item_vals = []
                    item_lat = None
                    item_lon = None

                    for c in item_cells:
                        if isinstance(c, dict):
                            t = c.get("t", "")
                            item_vals.append(t)

                            # ── EXTRACCIÓN EXHAUSTIVA DE COORDENADAS ──
                            candidates_lat = []
                            candidates_lon = []
                            for key in ("y", "lat", "latitude"):
                                if key in c and c[key]:
                                    try: candidates_lat.append(float(c[key]))
                                    except: pass
                            for key in ("x", "lon", "lng", "longitude"):
                                if key in c and c[key]:
                                    try: candidates_lon.append(float(c[key]))
                                    except: pass

                            nested_pos = c.get("pos") or c.get("p") or c.get("position")
                            if isinstance(nested_pos, dict):
                                for k in ("y", "lat"):
                                    if k in nested_pos and nested_pos[k]:
                                        try: candidates_lat.append(float(nested_pos[k]))
                                        except: pass
                                for k in ("x", "lon", "lng"):
                                    if k in nested_pos and nested_pos[k]:
                                        try: candidates_lon.append(float(nested_pos[k]))
                                        except: pass

                            if candidates_lat and candidates_lon:
                                item_lat = candidates_lat[0]
                                item_lon = candidates_lon[0]
                        else:
                            item_vals.append(str(c))

                    duracion = item_vals[-1] if item_vals else ""
                    dur_segundos = self._parse_duration_to_seconds(duracion)
                    dur_min = self._parse_duration_to_minutes(duracion)
                    total_sin_filtro += dur_min

                    # ═══════════════════════════════════════════════════════════
                    # ✅ FILTRO: SOLO eventos > 31 segundos
                    #    (30s o menos → 0 minutos efectivos, se descarta)
                    # ═══════════════════════════════════════════════════════════
                    if dur_segundos <= self.AP_MIN_EVENT_SECONDS:
                        evt = {
                            "duracion_min": round(dur_min, 2),
                            "duracion_seg": dur_segundos,
                            "zona": None,
                            "geocerca": None,
                            "lat": None,
                            "lon": None,
                            "tiene_gps": False,
                            "incluido": False,
                            "motivo_exclusion": f"Duración ≤ {self.AP_MIN_EVENT_SECONDS}s",
                            "minutos_redondeados": 0,
                        }
                        eventos_detalle.append(evt)
                        continue

                    # ── Fallback: coordenadas desde Plus Code / regex
                    if item_lat is None or item_lon is None:
                        for val in item_vals:
                            m = re.search(r'(-?\d+\.\d+)\s*[,;\s]+\s*(-?\d+\.\d+)', str(val))
                            if m:
                                try:
                                    a, b = float(m.group(1)), float(m.group(2))
                                    if -6 < a < -3 and -83 < b < -80:
                                        item_lat, item_lon = a, b
                                    elif -6 < b < -3 and -83 < a < -80:
                                        item_lat, item_lon = b, a
                                    break
                                except ValueError:
                                    pass

                    # ── GEOCERCA + FALLBACK ──────────────────────────────────
                    tiene_gps = (item_lat is not None and item_lon is not None)
                    dentro, zona_name, gf_name = False, None, None

                    if tiene_gps:
                        dentro, zona_name, gf_name = self._is_inside_allowed_geofence(item_lat, item_lon)
                    else:
                        # 🔴 FALLBACK: SIN COORDENADAS → INCLUIR evento
                        dentro = True
                        zona_name = "DESCONOCIDA"
                        gf_name = "Sin GPS"

                    # ═══════════════════════════════════════════════════════════
                    # ✅ REDONDEO INDIVIDUAL × 5 min (cada evento por separado)
                    # ═══════════════════════════════════════════════════════════
                    minutos_redondeados = 0
                    if dentro:
                        minutos_redondeados = int(dur_min / self.AP_ROUND_BLOCK_MINUTES) * self.AP_ROUND_BLOCK_MINUTES
                        if minutos_redondeados > 0:
                            total_parking_min += minutos_redondeados
                            zonas_acumulado[zona_name] = zonas_acumulado.get(zona_name, 0.0) + minutos_redondeados

                    evt = {
                        "duracion_min": round(dur_min, 2),
                        "duracion_seg": dur_segundos,
                        "zona": zona_name,
                        "geocerca": gf_name,
                        "lat": item_lat,
                        "lon": item_lon,
                        "tiene_gps": tiene_gps,
                        "incluido": dentro and minutos_redondeados > 0,
                        "motivo_exclusion": None if (dentro and minutos_redondeados > 0) else (
                            "Fuera de geocerca" if not dentro else "Redondeo a 0 min"
                        ),
                        "minutos_redondeados": minutos_redondeados,
                    }
                    eventos_detalle.append(evt)

        return total_parking_min, eventos_detalle, zonas_acumulado, total_sin_filtro

    def get_daily_parking_ap(self, wialon_names, timezone_offset=None):
        """
        Calcula el A.P. (Auxilio Público) para cada unidad basado en
        cronologías de estacionamiento del reporte INFORME DE PRODUCCION DIARIO.

        Lógica actualizada:
          1. Por CADA evento Parking, extraer coordenada y verificar si está
             dentro de las geocercas NORTE / CENTRO / SUR / ENACE.
          2. Sumar solo los minutos en zonas permitidas → parking_min.
          3. Redondear a bloques de 5 min → parking_rounded.
          4. Aplicar descuento 45 min → ap_min = max(0, parking_rounded - 45).

        Args:
            wialon_names: lista de nombres de unidad tal como aparecen en Wialon.
            timezone_offset: offset horario (default -5 para Perú).

        Returns:
            dict {nombre_wialon: {
                "parking_min": float,
                "parking_rounded": int,
                "ap_min": int,
                "zonas": {str: float},
                "eventos": list
            }}
        """
        if not self.sid and not self.login():
            return {}

        tz_offset = timezone_offset if timezone_offset is not None else self.TIMEZONE_OFFSET
        tz = timezone(timedelta(hours=tz_offset))
        now = datetime.now(tz)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=0)
        t_from = int(start.timestamp())
        t_to = int(end.timestamp())

        normalize = lambda s: " ".join(s.split()).upper()
        norm_targets = {normalize(n): n for n in wialon_names}

        debug_info = [
            f"╔══════════════════════════════════════════════════╗",
            f"║   CONSULTA A.P. CON FILTRO DE GEOCERCAS         ║",
            f"╠══════════════════════════════════════════════════╣",
            f"║ Fecha : {now.strftime('%Y-%m-%d %H:%M:%S')}",
            f"║ Rango : 00:00 – 23:59 hora local",
            f"║ Descuento: {self.AP_DISCOUNT_MINUTES} min",
            f"║ Redondeo : bloques de {self.AP_ROUND_BLOCK_MINUTES} min",
            f"╚══════════════════════════════════════════════════╝"
        ]

        resource_id = self.REPORT_RESOURCE_ID
        template_id = self.REPORT_TEMPLATE_ID
        ap_data = {}

        try:
            all_units = self._get_all_units()

            for item in all_units:
                name = item.get("nm", "")
                norm_name = normalize(name)

                if norm_name not in norm_targets:
                    continue

                orig_name = norm_targets[norm_name]
                unit_id = item.get("id")
                debug_info.append(f"\n{'─'*54}")
                debug_info.append(f"  🚗 UNIDAD: {name}  (ID: {unit_id})")
                debug_info.append(f"  {'─'*52}")

                try:
                    self._cleanup_report()
                    result = self._exec_report(resource_id, template_id, unit_id, t_from, t_to)

                    tables = result.get("reportResult", {}).get("tables", [])
                    if not tables:
                        debug_info.append("  ⚠️  Sin tablas en reporte → A.P. = 0")
                        ap_data[orig_name] = {
                            "parking_min": 0, "parking_rounded": 0,
                            "ap_min": 0, "zonas": {}, "eventos": []
                        }
                        continue

                    # Buscar tabla CRONOLOGIAS
                    chrono_idx = None
                    for idx, t in enumerate(tables):
                        if "CRONOLOG" in t.get("label", "").upper():
                            chrono_idx = idx
                            break

                    if chrono_idx is None:
                        debug_info.append("  ⚠️  No se encontró tabla CRONOLOGIAS → A.P. = 0")
                        ap_data[orig_name] = {
                            "parking_min": 0, "parking_rounded": 0,
                            "ap_min": 0, "zonas": {}, "eventos": []
                        }
                        continue

                    # Extraer minutos FILTRADOS por geocerca
                    parking_min, eventos, zonas, total_sin_filtro = self._get_parking_minutes_from_report(
                        chrono_idx, tables
                    )

                    # ── Estadística por zona ──
                    total_eventos = len(eventos)
                    eventos_ok = sum(1 for e in eventos if e["incluido"])
                    eventos_sin_gps = sum(1 for e in eventos if not e.get("tiene_gps", False))
                    eventos_cortos = sum(1 for e in eventos if (e.get("motivo_exclusion") or "").startswith("Duración"))
                    eventos_fuera_zona = sum(1 for e in eventos if e.get("motivo_exclusion") == "Fuera de geocerca")

                    debug_info.append(f"  📊 Eventos Estacionamiento totales: {total_eventos}")
                    debug_info.append(f"  ⏱️  Total SIN filtro          : {total_sin_filtro:.2f} min (bruto, sin reglas)")
                    debug_info.append(f"  ⏭️  Eventos descartados (<=31s): {eventos_cortos}")
                    debug_info.append(f"  🚫 Eventos fuera de geocerca  : {eventos_fuera_zona}")
                    debug_info.append(f"  ✅ Eventos que SÍ se suman    : {eventos_ok}")
                    debug_info.append(f"  📍 Eventos SIN coordenadas   : {eventos_sin_gps} (incluidos via fallback)")
                    if zonas:
                        for z, mins in sorted(zonas.items()):
                            debug_info.append(f"     ▸ Zona [{z}]: {int(mins)} min (suma de redondeos individuales)")

                    # ══════════════════════════════════════════════════════════
                    # NUEVA LÓGICA (sin descuento):
                    #   parking_min      = ya es la SUMA de redondeos individuales
                    #   parking_rounded  = idem (no hay segundo redondeo, se mantiene
                    #                       el nombre para compatibilidad con controller)
                    #   ap_min           = TOTAL FINAL (SIN descuento)
                    # ══════════════════════════════════════════════════════════
                    parking_rounded = int(parking_min)
                    ap_min = parking_rounded  # ✅ Sin descuento

                    debug_info.append(f"")
                    debug_info.append(f"  ┌{'─'*52}")
                    debug_info.append(f"  │ CÁLCULO FINAL (SIN DESCUENTO)")
                    debug_info.append(f"  ├{'─'*52}")
                    debug_info.append(f"  │  TOTAL (suma redondeos individuales × 5min)  = {parking_min:.0f} min")
                    debug_info.append(f"  │  Sin descuento (pedido usuario)              = − 0 min")
                    debug_info.append(f"  ├{'─'*52}")
                    debug_info.append(f"  │  🎯  A.P. FINAL = {ap_min} min")
                    debug_info.append(f"  └{'─'*52}")

                    # Detalle de cada evento (primeros 20 en log)
                    debug_info.append(f"")
                    debug_info.append(f"  ┌{'─'*62}")
                    debug_info.append(f"  │ Detalle de eventos (primeros 20)")
                    debug_info.append(f"  │ {'#':>3}  {'Duración':<10}  {'Seg':>5}  {'RD×5':>5}  {'Estado':<14}  Zona / Motivo")
                    debug_info.append(f"  └{'─'*62}")
                    for idx_e, evt in enumerate(eventos[:20], start=1):
                        dur_str = f"{evt['duracion_min']:.1f}min"
                        seg = evt.get("duracion_seg", 0)
                        rd = evt.get("minutos_redondeados", 0)
                        if evt["incluido"]:
                            mark = "✅ SUMA"
                            info_zona = evt["zona"] or "—"
                        else:
                            motivo = evt.get("motivo_exclusion") or ""
                            if motivo.startswith("Duración"):
                                mark = "⏭️  CORTO"
                                info_zona = motivo
                            elif motivo == "Fuera de geocerca":
                                mark = "🚫 FUERA"
                                info_zona = motivo
                            else:
                                mark = "❌ DESCARTADO"
                                info_zona = motivo
                        debug_info.append(
                            f"  {idx_e:>3}  {dur_str:<10}  {seg:>5}  {rd:>5}  {mark:<14}  {info_zona}"
                        )
                    if len(eventos) > 20:
                        debug_info.append(f"  ... (+{len(eventos)-20} eventos más)")

                    ap_data[orig_name] = {
                        "parking_min": round(parking_min, 2),
                        "parking_rounded": parking_rounded,
                        "ap_min": ap_min,
                        "zonas": {z: round(m, 2) for z, m in zonas.items()},
                        "eventos": eventos,
                        "total_sin_filtro": round(total_sin_filtro, 2)
                    }

                except Exception as e:
                    debug_info.append(f"  ❌ Error procesando unidad: {e}")
                    self.logger.error(f"Error procesando AP unidad {name}: {e}")
                    ap_data[orig_name] = {
                        "parking_min": 0, "parking_rounded": 0,
                        "ap_min": 0, "zonas": {}, "eventos": []
                    }

            # ── Guardar log de depuración ──
            try:
                with open("wialon_ap_debug.log", "w", encoding="utf-8") as f:
                    f.write("\n".join(debug_info))
                    f.write("\n\n═══════════════════════════════════════════════════════════════\n")
                    f.write("RESUMEN POR UNIDAD\n")
                    f.write("═══════════════════════════════════════════════════════════════\n")
                    f.write(f"  {'UNIDAD':<30} {'SIN FILTRO':>10} {'SUMADO':>8} {'RD×5':>5} {'AP':>4}  ZONAS\n")
                    f.write(f"  {'─'*30} {'─'*10} {'─'*8} {'─'*5} {'─'*4}  {'─'*30}\n")
                    for nm, d in ap_data.items():
                        zonas_str = ", ".join(f"{z}={v:.0f}" for z, v in d["zonas"].items()) or "—"
                        sf = d.get("total_sin_filtro", d["parking_min"])
                        f.write(f"  {nm:<30} {sf:>9.1f}  {d['parking_min']:>7.1f}  {d['parking_rounded']:>4d}  {d['ap_min']:>3d}  {zonas_str}\n")
            except Exception as e:
                self.logger.warning(f"No se pudo escribir wialon_ap_debug.log: {e}")

            return ap_data

        except Exception as e:
            self.logger.error(f"Error en get_daily_parking_ap: {e}")
            try:
                with open("wialon_ap_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"\n\n!!! EXCEPCIÓN GENERAL: {e}\n")
            except Exception:
                pass
            return {}

    def get_address(self, lat, lon):
        """
        Geocodificación inversa usando el servicio dedicado de Wialon (geocode-maps).
        """
        if not self.sid:
            return "Ubicación desconocida"
        
    def _get_local_talara_area(self, lat, lon):
        """
        Determina la ubicación exacta (Parque, Calle o Avenida) de Talara.
        """
        # Base de datos expandida para cubrir sectores alejados como Enace / Talara Alta
        TALARA_POIS = [
            # Sector ENACE / Talara Alta / Cono Sur
            {"name": "ENACE I", "lat": -4.5912, "lon": -81.1763},
            {"name": "ENACE II", "lat": -4.5950, "lon": -81.1830},
            {"name": "POSTA ENACE II", "lat": -4.5945, "lon": -81.1812},
            {"name": "URB. ENACE", "lat": -4.5930, "lon": -81.1850},
            {"name": "ALAN GARCIA", "lat": -4.5950, "lon": -81.1800},
            {"name": "28 DE JULIO", "lat": -4.5930, "lon": -81.1850},
            {"name": "NEGREIROS", "lat": -4.5831, "lon": -81.1878},
            {"name": "MARIO AGUIRRE", "lat": -4.5880, "lon": -81.2500},
            {"name": "MARUJA CABRERO", "lat": -4.5906, "lon": -81.2498},
            {"name": "JORGE CHAVEZ", "lat": -4.5943, "lon": -81.2484},
            
            # Centro y Parques
            {"name": "BASE", "lat": -4.5876, "lon": -81.2695},
            {"name": "PLAZA GRAU", "lat": -4.5772, "lon": -81.2715},
            {"name": "MERCADO MODELO", "lat": -4.5765, "lon": -81.2705},
            {"name": "LA PARADA", "lat": -4.5865, "lon": -81.2692},
            {"name": "MERCADO ACAPULCO", "lat": -4.5728, "lon": -81.2732},
            {"name": "PLAZUELA EL PESCADOR", "lat": -4.5620, "lon": -81.2747},
            {"name": "DOMINGO SAVIO", "lat": -4.5810, "lon": -81.2720},
            {"name": "PARQUE 62", "lat": -4.5799, "lon": -81.2741},
            {"name": "PARQUE 35", "lat": -4.5805, "lon": -81.2730},
            {"name": "AV. PARQUE 59-33", "lat": -4.5815, "lon": -81.2740}, 
            {"name": "PARQUE 47", "lat": -4.5862, "lon": -81.2718},
            {"name": "PLAZA VEA / CENTRO", "lat": -4.5815, "lon": -81.2618},
            {"name": "LOS TRONCOS", "lat": -4.5780, "lon": -81.2700},
            
            # Urbanizaciones y Avenidas
            {"name": "VILLA TALARA", "lat": -4.5876, "lon": -81.2646},
            {"name": "SAN SEBASTIAN", "lat": -4.5873, "lon": -81.2663},
            {"name": "NUEVA TALARA", "lat": -4.5850, "lon": -81.2550},
            {"name": "URB. SUDAMÉRICA", "lat": -4.5885, "lon": -81.2725},
            {"name": "VILLA FAP", "lat": -4.5810, "lon": -81.2585},
            {"name": "URB. POPULAR", "lat": -4.5785, "lon": -81.2565},
            {"name": "URB. LOS PINOS", "lat": -4.5795, "lon": -81.2505},
            {"name": "PARQUE CRISTO MIRADOR", "lat": -4.5815, "lon": -81.2492},
            {"name": "ABELARDO QUIÑONES", "lat": -4.5820, "lon": -81.2500},
            {"name": "SAN MARTIN DE PORRES", "lat": -4.5800, "lon": -81.2550},
            {"name": "LAS PEÑITAS", "lat": -4.5667, "lon": -81.2833},
            {"name": "PUENTE YALE", "lat": -4.5665, "lon": -81.2675},
            
            # Tramos de Av. F y Otros
            {"name": "AV. F", "lat": -4.5825, "lon": -81.2785},
            {"name": "AV. F", "lat": -4.5845, "lon": -81.2715},
            {"name": "AV. F", "lat": -4.5910, "lon": -81.2685},
            {"name": "AV. D 30", "lat": -4.5775, "lon": -81.2735},
            {"name": "AV. H", "lat": -4.5815, "lon": -81.2725},
            {"name": "AV. A", "lat": -4.5885, "lon": -81.2580},
            {"name": "AV. YALE", "lat": -4.5665, "lon": -81.2675},
            {"name": "AV. BOLOGNESI", "lat": -4.5710, "lon": -81.2725},
            {"name": "AH LUCY DE VILLANUEVA", "lat": -4.5635, "lon": -81.2745},
            {"name": "MIRADOR CRISTO PETROLERO", "lat": -4.5815, "lon": -81.2605},
            {"name": "CALLE 1", "lat": -4.5875, "lon": -81.2715},
            {"name": "CALLE C1", "lat": -4.5895, "lon": -81.2665},
            {"name": "7 DE JUNIO", "lat": -4.5935, "lon": -81.2655},
        ]

        closest_poi = "TALARA"
        min_dist = 1.0  # Radio ampliado para capturar sectores alejados como Enace

        for poi in TALARA_POIS:
            dist = _haversine(lat, lon, poi["lat"], poi["lon"])
            if dist < min_dist:
                min_dist = dist
                closest_poi = poi["name"]

        # Si no hay nada cerca dentro de 1km, usar jurisdicción base como último recurso
        if closest_poi == "TALARA":
            return _get_jurisdiction(lat, lon)
            
        return closest_poi

    def _get_detailed_address(self, lat, lon):
        """
        Obtiene dirección detallada usando Nominatim (OSM) para coordenadas específicas.
        Retorna calle/avenida, urbanización, distrito.
        """
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            headers = {"User-Agent": "SerenazgoTalara/1.0"}
            params = {
                "lat": lat,
                "lon": lon,
                "format": "jsonv2",
                "zoom": 18,
                "addressdetails": 1
            }
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if "address" in data:
                    addr = data["address"]
                    # Construir dirección legible
                    parts = []
                    if addr.get("road"): parts.append(addr["road"])
                    if addr.get("suburb"): parts.append(addr["suburb"])
                    if addr.get("neighbourhood"): parts.append(addr["neighbourhood"])
                    if addr.get("city"): parts.append(addr["city"])
                    
                    if parts:
                        return ", ".join(parts)
            return "Dirección no disponible"
        except Exception as e:
            self.logger.warning(f"Error geocodificación detallada: {e}")
            return "Dirección no disponible"

    def get_address(self, lat, lon):
        """
        Retorna la ubicación local de Talara basada en geocodificador interno.
        """
        try:
            sector = self._get_local_talara_area(lat, lon)
            return sector
        except Exception:
            return "UBICACIÓN DESCONOCIDA"

    def _force_update_unit(self, unit_id):
        """Fuerza la actualización de los datos de una unidad (para obtener posición más reciente)."""
        params = {
            "svc": "core/update_data_flags",
            "params": json.dumps({
                "itemId": unit_id,
                "flags": 0x00000400  # Flag para actualizar mensajes
            }),
            "sid": self.sid
        }
        try:
            requests.get(self.real_base_url, params=params, timeout=10)
        except Exception:
            pass  # No crítico si falla

    def get_units_realtime_status(self, wialon_names, detailed=False):
        """
        Consulta velocidad y ubicación actual FORZANDO actualización.
        Retorna timestamp y antigüedad internamente (no se muestra al usuario por defecto).
        """
        if not self.sid and not self.login():
            return {}

        normalize = lambda s: " ".join(s.split()).upper()
        norm_targets = {normalize(n): n for n in wialon_names}

        # PASO 1: Obtener IDs de las unidades
        params_ids = {
            "svc": "core/search_items",
            "params": json.dumps({
                "spec": {
                    "itemsType": "avl_unit",
                    "propName": "sys_name",
                    "propValueMask": "*",
                    "sortType": "sys_name"
                },
                "force": 1,
                "flags": 1,  # solo id y nombre
                "from": 0,
                "to": 0
            }),
            "sid": self.sid
        }
        resp = requests.get(self.real_base_url, params=params_ids, timeout=15)
        items = resp.json().get("items", [])

        unit_ids = {}
        for item in items:
            name = item.get("nm", "")
            norm_name = normalize(name)
            if norm_name in norm_targets:
                orig_name = norm_targets[norm_name]
                unit_ids[orig_name] = item["id"]

        # PASO 2: Forzar actualización para cada unidad
        for unit_id in unit_ids.values():
            self._force_update_unit(unit_id)

        # PASO 3: Consultar datos actualizados con lmsg (flags 1|1024)
        params = {
            "svc": "core/search_items",
            "params": json.dumps({
                "spec": {
                    "itemsType": "avl_unit",
                    "propName": "sys_name",
                    "propValueMask": "*",
                    "sortType": "sys_name"
                },
                "force": 1,
                "flags": 1 | 1024,  # 1024 incluye lmsg (último mensaje)
                "from": 0,
                "to": 0
            }),
            "sid": self.sid
        }

        realtime_data = {}
        try:
            response = requests.get(self.real_base_url, params=params, timeout=15)
            items = response.json().get("items", [])

            for item in items:
                name = item.get("nm", "")
                norm_name = normalize(name)

                if norm_name in norm_targets:
                    orig_name = norm_targets[norm_name]
                    lmsg = item.get("lmsg", {})
                    pos = lmsg.get("pos", {})

                    if pos:
                        speed = pos.get("s", 0)
                        lat, lon = pos.get("y"), pos.get("x")
                        timestamp = lmsg.get("t", 0)

                        # Calcular antigüedad y hora local
                        peru_tz = timezone(timedelta(hours=self.TIMEZONE_OFFSET))
                        utc_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                        local_time = utc_time.astimezone(peru_tz)
                        hora_local = local_time.strftime("%Y-%m-%d %H:%M:%S")
                        ahora_local = datetime.now(peru_tz)
                        antiguedad_min = (ahora_local - local_time).total_seconds() / 60.0

                        status = "P" if speed > self.MIN_SPEED_KMH else "T"
                        address = self.get_address(lat, lon)
                        full_address = self._get_detailed_address(lat, lon)

                        if detailed:
                            realtime_data[orig_name] = {
                                "status": status,
                                "address": address,
                                "full_address": full_address,
                                "lat": lat,
                                "lon": lon,
                                "speed": speed,
                                "timestamp": timestamp,
                                "hora_local": hora_local,
                                "antiguedad_min": round(antiguedad_min, 1),
                                "es_reciente": antiguedad_min < 5
                            }
                        else:
                            # Modo legacy (sin hora en texto visible)
                            realtime_data[orig_name] = f"{status}. {full_address}"
                    else:
                        if detailed:
                            realtime_data[orig_name] = {
                                "status": "?",
                                "address": "Sin señal GPS",
                                "full_address": "Sin señal GPS",
                                "lat": None,
                                "lon": None,
                                "speed": 0,
                                "timestamp": 0,
                                "hora_local": "",
                                "antiguedad_min": 0,
                                "es_reciente": False
                            }
                        else:
                            realtime_data[orig_name] = "Sin señal GPS"

            # Guardar log de depuración
            try:
                with open("wialon_realtime_debug.json", "w", encoding="utf-8") as f:
                    log_data = {}
                    for name, data in realtime_data.items():
                        if isinstance(data, dict):
                            log_data[name] = {
                                "lat": data.get("lat"),
                                "lon": data.get("lon"),
                                "timestamp": data.get("timestamp"),
                                "hora_local": data.get("hora_local"),
                                "speed": data.get("speed")
                            }
                    json.dump(log_data, f, indent=2, ensure_ascii=False)
            except:
                pass

            return realtime_data
        except Exception as e:
            self.logger.error(f"Error en get_units_realtime_status: {e}")
            return {}

    def logout(self):
        if self.sid:
            try:
                requests.get(self.real_base_url, params={"svc": "core/logout", "sid": self.sid}, timeout=10)
            except Exception:
                pass
            self.sid = None

    # ------------------------------------------------------------------
    # ENRIQUECIMIENTO DE DIRECCIONES Y CLASIFICACION TALARA
    # ------------------------------------------------------------------

    def _is_plus_code(self, address_str):
        """
        Determina si un texto es probablemente un código Plus Code como 'CQ62+95M'
        """
        if not address_str or not isinstance(address_str, str):
            return False
        # Buscamos un patrón básico de plus code (4 a 8 caracteres alfanuméricos) + "+" + (2 o más)
        is_plus_format = bool(re.search(r'[23456789C]+[+CcGgDdFfHhJjKkLlMmRrTtVvWw]+\w*', address_str))
        has_short_plus = "+" in address_str and len(address_str.split("+")[0]) <= 8
        return is_plus_format or has_short_plus

    def _geocode_fallback(self, lat, lon, google_api_key=None):
        """
        Fallback a proveedor externo. 
        Prioridad 1: Google Maps (si se provee la API Key)
        Prioridad 2: Nominatim OSM
        """
        if google_api_key:
            try:
                url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={google_api_key}"
                resp = requests.get(url, timeout=5)
                data = resp.json()
                if data.get("status") == "OK" and data.get("results"):
                    return data["results"][0]["formatted_address"]
            except Exception as e:
                self.logger.error(f"Error Google Geocode Fallback: {e}")
        
        # Fallback a Nominatim (OSM)
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            headers = {"User-Agent": "SerenazgoTalara/1.0"}
            params = {
                "lat": lat,
                "lon": lon,
                "format": "jsonv2",
                "zoom": 18
            }
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if "address" in data:
                    addr = data["address"]
                    road = addr.get("road", "")
                    suburb = addr.get("suburb", "")
                    city = addr.get("city", addr.get("town", addr.get("city_district", "Talara")))
                    postcode = addr.get("postcode", "")
                    country = addr.get("country", "Perú")
                    
                    parts = []
                    if road: parts.append(road)
                    if suburb: parts.append(suburb)
                    # Añadir ciudad y postcode
                    city_part = f"{city} {postcode}".strip()
                    if city_part: parts.append(city_part)
                    if country: parts.append(country)
                    
                    res = ", ".join([p for p in parts if p]).strip()
                    if res:
                        return res
        except Exception as e:
            self.logger.error(f"Error Nominatim OSM Fallback: {e}")

        return None

    def _classify_talara_zone(self, lat, lon):
        """
        Clasifica las coordenadas dentro de Talara Baja o Alta y retorna el sector exacto.
        """
        TALARA_BAJA = [
            {"name": "Av. Bolognesi", "lat": -4.5710, "lon": -81.2725},
            {"name": "Av. Grau", "lat": -4.5772, "lon": -81.2715},
            {"name": "Av. G", "lat": -4.5794, "lon": -81.2750},
            {"name": "Av. H", "lat": -4.5815, "lon": -81.2725},
            {"name": "Ignacio Merino", "lat": -4.5760, "lon": -81.2740},
            {"name": "San Pedro", "lat": -4.5685, "lon": -81.2770},
            {"name": "Maruja Sullón", "lat": -4.5700, "lon": -81.2800},
            {"name": "Las Peñitas", "lat": -4.5667, "lon": -81.2833},
            {"name": "Santa Rita", "lat": -4.5645, "lon": -81.2775},
            {"name": "Lucy de Villanueva", "lat": -4.5635, "lon": -81.2745},
            {"name": "Villa Talara", "lat": -4.5876, "lon": -81.2646},
            {"name": "Urb. Sudamérica", "lat": -4.5885, "lon": -81.2725},
            {"name": "Aproviser", "lat": -4.5900, "lon": -81.2755},
            {"name": "Vencedores", "lat": -4.5620, "lon": -81.2790},
            {"name": "Punta Arenas", "lat": -4.5650, "lon": -81.2860},
            {"name": "Centro", "lat": -4.5765, "lon": -81.2705}
        ]
        
        TALARA_ALTA = [
            {"name": "Mártires de la Paz", "lat": -4.5815, "lon": -81.2585},
            {"name": "Av. B", "lat": -4.5880, "lon": -81.2620},
            {"name": "Av. C", "lat": -4.5855, "lon": -81.2650},
            {"name": "Av. D", "lat": -4.5775, "lon": -81.2735},
            {"name": "Av. E", "lat": -4.5830, "lon": -81.2670},
            {"name": "Av. F", "lat": -4.5825, "lon": -81.2785},
            {"name": "Av. Perú", "lat": -4.5920, "lon": -81.2550},
            {"name": "Abelardo Quiñones", "lat": -4.5820, "lon": -81.2500},
            {"name": "Jesús María", "lat": -4.5840, "lon": -81.2480},
            {"name": "Jorge Chávez", "lat": -4.5943, "lon": -81.2484},
            {"name": "Sol de Oro", "lat": -4.5870, "lon": -81.2450},
            {"name": "Nuevo Horizonte", "lat": -4.5900, "lon": -81.2420},
            {"name": "Pilar Nores", "lat": -4.5910, "lon": -81.2390},
            {"name": "Micaela Bastidas", "lat": -4.5950, "lon": -81.2520},
            {"name": "Los Ficus", "lat": -4.5980, "lon": -81.2500},
            {"name": "Las Gardenias", "lat": -4.5965, "lon": -81.2470},
            {"name": "San Martín de Porres", "lat": -4.5800, "lon": -81.2550},
            {"name": "ENACE", "lat": -4.5930, "lon": -81.1850}
        ]
        
        min_dist_baja = 999.0
        closest_baja = ""
        for zone in TALARA_BAJA:
            d = _haversine(lat, lon, zone["lat"], zone["lon"])
            if d < min_dist_baja:
                min_dist_baja = d
                closest_baja = zone["name"]
                
        min_dist_alta = 999.0
        closest_alta = ""
        for zone in TALARA_ALTA:
            d = _haversine(lat, lon, zone["lat"], zone["lon"])
            if d < min_dist_alta:
                min_dist_alta = d
                closest_alta = zone["name"]
                
        # Tolerancia 2.5 km a la redonda
        if min_dist_alta < min_dist_baja and min_dist_alta < 2.5:
            return f"{closest_alta} (Talara Alta)"
        elif min_dist_baja < 2.5:
            return f"{closest_baja} (Talara Baja)"
        
        return ""

    def _geocode_wialon_batch(self, coords_list):
        """
        Geocodifica una lista de tuplas (lat, lon) usando core/batch + core/search_address.
        """
        if not coords_list or not self.sid:
            return [None] * len(coords_list)
            
        try:
            params_list = []
            for lat, lon in coords_list:
                if lat is None or lon is None:
                    # Enviar vacíos si no hay coord
                    params_list.append({
                        "svc": "core/search_address",
                        "params": {"y": 0, "x": 0, "flags": 0}
                    })
                else:
                    params_list.append({
                        "svc": "core/search_address",
                        "params": {"y": lat, "x": lon, "flags": 0} # 0 o formato necesario por API
                    })
                    
            batch_req = {
                "svc": "core/batch",
                "params": json.dumps({
                    "params": params_list,
                    "flags": 0
                }),
                "sid": self.sid
            }
            
            resp = requests.post(self.real_base_url, data=batch_req, timeout=30)
            data = resp.json()
            
            addresses = []
            if isinstance(data, list):
                for res in data:
                    if isinstance(res, str):
                        addresses.append(res)
                    elif isinstance(res, dict) and "address" in res:
                        addresses.append(res["address"])
                    elif isinstance(res, dict) and "error" in res:
                        # Error de batch en subconsulta
                        addresses.append("")
                    else:
                        addresses.append("")
            else:
                addresses = [""] * len(coords_list)
                
            return addresses
            
        except Exception as e:
            self.logger.error(f"Error en Wialon geocode batch: {e}")
            return [""] * len(coords_list)

    def enrich_report_locations(self, report_records, google_api_key=None):
        """
        Toma una lista de registros tipo tabla, resuelve sus direcciones usando la API de Wialon
        (usando 'core/search_address'), o un fallback Nominatim / Google, filtrando Plus Codes 
        y empaquetando todo acorde a las zonas geográficas de Talara.

        Se espera: 
            report_records = [
                {"lat_inicial": -4.x, "lon_inicial": -81.y, "lat_final": -4.a, "lon_final": -81.b, "duracion": "0:45:00"},
                ...
            ]
        """
        if not report_records:
            return []

        # 1. Empaquetar coordenadas (pares inicial/final consecutivos)
        coords_list = []
        for rec in report_records:
            coords_list.append((rec.get("lat_inicial"), rec.get("lon_inicial")))
            coords_list.append((rec.get("lat_final"), rec.get("lon_final")))
            
        # 2. Consultar Wialon Batch
        wialon_addresses = self._geocode_wialon_batch(coords_list)
        
        # 3. Procesar y enriquecer cada registro
        for i, rec in enumerate(report_records):
            for t_idx, prefix in [(0, "inicial"), (1, "final")]:
                idx = (i * 2) + t_idx
                lat, lon = coords_list[idx]
                
                if lat is None or lon is None or lat == 0:
                    rec[f"ubicacion_{prefix}"] = "Sin ubicación GPS"
                    continue
                    
                addr_raw = wialon_addresses[idx] if idx < len(wialon_addresses) else ""
                
                # Descartar si es código Plus o está vacío
                if self._is_plus_code(addr_raw) or not addr_raw:
                    # Usar fallback
                    addr_fallback = self._geocode_fallback(lat, lon, google_api_key)
                    if addr_fallback:
                        addr_raw = addr_fallback
                        if not google_api_key:
                            # Pausa corta requerida por Nominatim
                            time.sleep(0.6) 

                # Clasificar con la red urbana de Talara
                talara_zone = self._classify_talara_zone(lat, lon)
                
                if talara_zone:
                    # Mezclar: Evitamos repeticiones. EJ: "Av. F (Talara Alta) - Av. F" -> "Av. F (Talara Alta)"
                    zone_name_clean = talara_zone.split("(")[0].strip()
                    if zone_name_clean in str(addr_raw):
                        final_address = f"{addr_raw} ({talara_zone.split('(')[-1]}"
                    else:
                        # Si no menciona Talara en crudo, la concatenamos
                        if "Talara" not in str(addr_raw):
                            final_address = f"{talara_zone}, {addr_raw}".strip(", ")
                        else:
                            final_address = f"{talara_zone} - {addr_raw}"
                else:
                    final_address = addr_raw if addr_raw else "Ubicación desconocida"
                    
                # Formalizar la cola
                if final_address and "Talara" not in final_address and final_address != "Sin ubicación GPS":
                   final_address += ", Talara, Perú"
                
                rec[f"ubicacion_{prefix}"] = final_address

        return report_records
