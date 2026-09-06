# controller.py (versión ULTRA-OPTIMIZADA)
import os
import socket
import time
import tkinter as tk
from datetime import datetime, timedelta, timezone
from tkinter import ttk
from tkinter import messagebox
from megafonos import abrir_ventana_megafonos
import webbrowser
from wialon_api import WialonAPI
import winsound # Solo para Windows
import warnings
import threading
from concurrent.futures import ThreadPoolExecutor

# Third-party imports
import ntplib
import pyperclip
import pytz 
import shutil

# Imports for printing functionality
try:
    from PIL import Image
    import win32clipboard
except ImportError:
    Image = None
    win32clipboard = None
    print("Advertencia: PIL o win32clipboard no disponibles para funcionalidad de impresión")

# Importar módulos centralizados
from utils import ToastNotification, Validators, LoadingDialog, resource_manager

class AdvancedNTPTimeService:
    """Servicio avanzado de tiempo NTP con failover inteligente y caché."""
    
    def __init__(self):
        self.ntp_servers = [
            'time.windows.com',
            'time.google.com',
            'time.cloudflare.com', 
            'pool.ntp.org',
            'time.apple.com',
            'time.nist.gov'
        ]
        self.timeout = 2  # segundos
        self.last_known_time = None
        self.timezone = pytz.timezone('America/Lima')
        self.last_ntp_update = None
        self.ntp_cache_ttl = 300  # 5 minutos en segundos
        self.server_performance = {}  # Tracking de rendimiento por servidor
        self._lock = threading.Lock()
        
    def get_network_time(self):
        """Obtiene el tiempo de red con failover inteligente."""
        with self._lock:
            # Verificar caché primero
            if (self.last_ntp_update and 
                time.time() - self.last_ntp_update < self.ntp_cache_ttl):
                return self.last_known_time
            
            # Intentar servidores en orden de rendimiento
            sorted_servers = self._get_sorted_servers()
            
            for server in sorted_servers:
                try:
                    ntp_client = ntplib.NTPClient()
                    response = ntp_client.request(server, timeout=self.timeout)
                    
                    if response.offset:
                        # Convertir a zona horaria local
                        utc_time = datetime.fromtimestamp(response.tx_time, tz=timezone.utc)
                        local_time = utc_time.astimezone(self.timezone)
                        
                        # Actualizar caché y rendimiento
                        self.last_known_time = local_time
                        self.last_ntp_update = time.time()
                        self._update_server_performance(server, response.delay, True)
                        
                        return local_time
                        
                except Exception as e:
                    self._update_server_performance(server, 5.0, False)
                    continue
            
            # Si todos fallan, usar tiempo local
            if not self.last_known_time:
                self.last_known_time = datetime.now(self.timezone)
            
            return self.last_known_time
    
    def _get_sorted_servers(self):
        """Obtiene servidores ordenados por rendimiento."""
        def server_score(server):
            perf = self.server_performance.get(server, {'success_rate': 0.5, 'avg_response': 5.0})
            return perf['success_rate'] * (1.0 / max(perf['avg_response'], 0.1))
        
        return sorted(self.ntp_servers, key=server_score, reverse=True)
    
    def _update_server_performance(self, server, response_time, success):
        """Actualiza métricas de rendimiento del servidor."""
        if server not in self.server_performance:
            self.server_performance[server] = {
                'success_rate': 0.5,
                'avg_response': response_time,
                'attempts': 0
            }
        
        perf = self.server_performance[server]
        attempts = perf['attempts'] + 1
        
        # Actualizar tasa de éxito
        if success:
            perf['success_rate'] = (perf['success_rate'] * (attempts - 1) + 1.0) / attempts
        else:
            perf['success_rate'] = perf['success_rate'] * 0.9
        
        # Actualizar tiempo de respuesta promedio
        perf['avg_response'] = (perf['avg_response'] * (attempts - 1) + response_time) / attempts
        perf['attempts'] = attempts

class OptimizedController:
    """Controlador optimizado con mejor rendimiento y nuevas funcionalidades."""
    
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.gestion_unidades = None
        self.time_service = AdvancedNTPTimeService()
        self.editing_mode = False
        self.last_search_time = 0
        self.search_delay_ms = 200  # Reducido para mejor responsividad
        self.first_turno_update = True
        
        # Pool de threads unificado para operaciones no bloqueantes
        self.thread_pool = ThreadPoolExecutor(max_workers=3)
        resource_manager.register_thread(self.thread_pool)
        
        # Sistema de caché para operaciones frecuentes
        self._operation_cache = {}
        self._cache_lock = threading.Lock()
        
        # Configurar optimizaciones
        self._setup_optimizations()
    
    def _run_task_async(self, task_func, on_success=None, on_error=None, show_loading=True, loading_msg="Procesando..."):
        """Ejecuta una tarea en segundo plano con diálogo de carga opcional."""
        loading_dialog = None
        if show_loading:
            loading_dialog = LoadingDialog(self.view.root, message=loading_msg)
        
        def wrapper():
            try:
                # Ejecutar la tarea
                result = task_func()
                # Volver al hilo principal para actualizar la UI
                self.view.root.after(0, lambda: self._handle_task_result(result, on_success, loading_dialog))
            except Exception as e:
                # Manejar error en el hilo principal
                self.view.root.after(0, lambda: self._handle_task_error(e, on_error, loading_dialog))
        
        self.thread_pool.submit(wrapper)

    def _handle_task_result(self, result, on_success, loading_dialog):
        """Maneja el éxito de una tarea asíncrona."""
        if loading_dialog: loading_dialog.close()
        if on_success: on_success(result)

    def _handle_task_error(self, error, on_error, loading_dialog):
        """Maneja el error de una tarea asíncrona."""
        if loading_dialog: loading_dialog.close()
        print(f"[CONTROLLER] Error en tarea asíncrona: {error}")
        if on_error:
            on_error(error)
        else:
            self.view.show_message("Error", f"Ocurrió un error en la operación: {str(error)}", "error")
    
    def _setup_optimizations(self):
        """Configura optimizaciones del controlador."""
        # Configurar debouncing más eficiente
        self._debounce_timer = None
        
        # Configurar caché de validaciones usando la clase centralizada
        self._validation_cache = {}
        
        # Configurar sistema de callbacks optimizado
        self._callbacks = {
            'status_update': [],
            'counter_update': [],
            'data_change': []
        }
    
    def actualizar_vista_unidades(self):
        """Actualiza la vista después de cambios en las unidades con caché."""
        cache_key = f"vista_unidades_{self.view.get_filtro_var()}"
        
        with self._cache_lock:
            if cache_key in self._operation_cache:
                cached_time, cached_result = self._operation_cache[cache_key]
                if time.time() - cached_time < 5:  # Caché válido por 5 segundos
                    return
        
        # Actualizar vista
        self.view.update_unit_display(
            units_to_display=self.model.UNIDADES_DISPONIBLES,
            filter_type=self.view.get_filtro_var(),
            is_editing_mode=self.editing_mode
        )
        self.actualizar_contadores()
        
        # Actualizar caché
        with self._cache_lock:
            self._operation_cache[cache_key] = (time.time(), True)

    def force_time_update(self):
        """Fuerza una actualización inmediata del tiempo NTP de forma asíncrona."""
        def update_time():
            self.time_service.last_ntp_update = None
            self._actualizar_turno_logic()
            self.actualizar_reloj()
        
        # Ejecutar en thread separado para no bloquear UI
        self.thread_pool.submit(update_time)
        self.view.update_status("Actualizando hora desde servidores NTP...", "blue")

    def get_current_timezone(self):
        """Obtiene la zona horaria actualmente configurada"""
        return str(self.time_service.timezone)    

    def set_timezone(self, timezone_str):
        """Cambia la zona horaria utilizada"""
        try:
            self.time_service.timezone = pytz.timezone(timezone_str)
            self.force_time_update()
            self.view.update_status(f"Zona horaria cambiada a: {timezone_str}")
            return True
        except Exception as e:
            self.view.show_message("Error", f"No se pudo cambiar la zona horaria: {str(e)}", "error")
            return False

    def debounced_search(self):
        """Búsqueda con debouncing optimizado para mejor rendimiento."""
        current_time = time.time() * 1000
        self.last_search_time = current_time
        
        # Cancelar timer anterior si existe
        if self._debounce_timer:
            self.view.root.after_cancel(self._debounce_timer)
        
        # Programar nueva búsqueda
        self._debounce_timer = self.view.root.after(
            self.search_delay_ms, 
            lambda: self._execute_search(current_time)
        )
    
    def _execute_search(self, search_time):
        """Ejecuta la búsqueda si no ha sido supersedida."""
        if search_time == self.last_search_time:
            self._perform_search()
    
    def _perform_search(self):
        """Realiza la búsqueda optimizada con caché."""
        busqueda = self.view.get_busqueda_var().strip().lower()
        
        # Caché de resultados de búsqueda
        cache_key = f"search_{busqueda}"
        with self._cache_lock:
            if cache_key in self._operation_cache:
                cached_time, cached_result = self._operation_cache[cache_key]
                if time.time() - cached_time < 2:  # Caché de búsqueda por 2 segundos
                    filtered_units = cached_result
                else:
                    filtered_units = self._filter_units_by_search(busqueda)
                    self._operation_cache[cache_key] = (time.time(), filtered_units)
            else:
                filtered_units = self._filter_units_by_search(busqueda)
                self._operation_cache[cache_key] = (time.time(), filtered_units)
        
        if busqueda:
            self.view.update_unit_display(
                units_to_display=filtered_units,
                filter_type="SEARCH",
                is_editing_mode=self.editing_mode
            )
            self.view.update_status(f"Búsqueda: {len(filtered_units)} unidades encontradas", "blue")
        else:
            # Restaurar filtro anterior
            self.aplicar_filtro(self.view.get_filtro_var())
    
    def _filter_units_by_search(self, busqueda):
        """Filtra unidades por término de búsqueda con algoritmo optimizado."""
        if not busqueda:
            return self.model.UNIDADES_DISPONIBLES
        
        filtered = []
        search_terms = busqueda.split()  # Búsqueda por múltiples términos
        
        for alias in self.model.UNIDADES_DISPONIBLES:
            alias_lower = alias.lower()
            # Verificar si TODOS los términos están presentes
            if all(term in alias_lower for term in search_terms):
                filtered.append(alias)
        
        return filtered

    def aplicar_filtro(self, filtro_type, skip_manual_dialog=False):
        """Aplica filtros con caché y optimización."""
        cache_key = f"filter_{filtro_type}"
        
        with self._cache_lock:
            if cache_key in self._operation_cache:
                cached_time, cached_units = self._operation_cache[cache_key]
                if time.time() - cached_time < 10:  # Caché de filtros por 10 segundos
                    units_to_display = cached_units
                else:
                    units_to_display = self._get_filtered_units(filtro_type)
                    self._operation_cache[cache_key] = (time.time(), units_to_display)
            else:
                units_to_display = self._get_filtered_units(filtro_type)
                self._operation_cache[cache_key] = (time.time(), units_to_display)
        
        if filtro_type == "MANUAL":
            if skip_manual_dialog:
                # Aplicar filtro MANUAL sin abrir ventana de selección
                # Usar las unidades actualmente seleccionadas
                current_selected = self.view.get_selected_units()
                self.view.update_unit_display(
                    units_to_display=current_selected,
                    filter_type=filtro_type,
                    is_editing_mode=self.editing_mode,
                    selected_units_by_checkbox=current_selected
                )
            else:
                # Obtener las unidades actualmente seleccionadas en la vista principal
                current_selected = self.view.get_selected_units()
                selected_units = self.view.show_unit_selection_window(
                    self.model.UNIDADES_DISPONIBLES, current_selected
                )
                self.view.update_unit_display(
                    units_to_display=selected_units,
                    filter_type=filtro_type,
                    is_editing_mode=self.editing_mode,
                    selected_units_by_checkbox=selected_units
                )
        else:
            self.view.update_unit_display(
                units_to_display=units_to_display,
                filter_type=filtro_type,
                is_editing_mode=self.editing_mode
            )
        
        self.actualizar_contadores()
        self.view.update_status(f"Filtro aplicado: {filtro_type} ({len(units_to_display)} unidades)", "green")
    
    def _get_filtered_units(self, filtro_type):
        """Obtiene unidades filtradas según el tipo."""
        if filtro_type == "TODAS":
            return self.model.UNIDADES_DISPONIBLES[:]
        elif filtro_type == "PICKUP":
            return [alias for alias in self.model.UNIDADES_DISPONIBLES 
                   if self.model.ALIAS_UNIDADES.get(alias, alias.split(' / ')[1] if ' / ' in alias else alias) in self.model.CAMIONETAS]
        elif filtro_type == "AUTOS":
            return [alias for alias in self.model.UNIDADES_DISPONIBLES 
                   if self.model.ALIAS_UNIDADES.get(alias, alias.split(' / ')[1] if ' / ' in alias else alias) in self.model.AUTOS]
        elif filtro_type == "MANUAL":
            return []  # Se maneja por separado
        else:
            return self.model.UNIDADES_DISPONIBLES[:]

    def validar_entrada_campo(self, valor):
        """Validación optimizada usando la clase centralizada Validators."""
        if not valor:
            return True
        
        # Caché de validaciones para evitar recálculos
        if valor in self._validation_cache:
            return self._validation_cache[valor]
        
        # Usar la clase centralizada de validadores
        result = Validators.validate_numeric(valor, max_length=6)
        
        # Guardar en caché (limitado a 100 entradas)
        if len(self._validation_cache) < 100:
            self._validation_cache[valor] = result
        
        return result

    def actualizar_observaciones_gui(self, entry_km, entry_ap, entry_po, lbl_obs_km, lbl_obs_ap, lbl_obs_po):
        """Actualiza observaciones con validación optimizada."""
        try:
            km = entry_km.get()
            ap = entry_ap.get()
            po = entry_po.get()
            
            # Usar caché para evitar recálculos
            cache_key = f"obs_{km}_{ap}_{po}"
            with self._cache_lock:
                if cache_key in self._operation_cache:
                    cached_time, cached_obs = self._operation_cache[cache_key]
                    if time.time() - cached_time < 30:  # Caché de observaciones por 30 segundos
                        obs_km, obs_ap, obs_po = cached_obs
                    else:
                        obs_km, obs_ap, obs_po = self.model.calcular_observaciones(km, ap, po)
                        self._operation_cache[cache_key] = (time.time(), (obs_km, obs_ap, obs_po))
                else:
                    obs_km, obs_ap, obs_po = self.model.calcular_observaciones(km, ap, po)
                    self._operation_cache[cache_key] = (time.time(), (obs_km, obs_ap, obs_po))
            
            # Actualizar labels con colores mejorados
            self._update_observation_label(lbl_obs_km, obs_km)
            self._update_observation_label(lbl_obs_ap, obs_ap) 
            self._update_observation_label(lbl_obs_po, obs_po)
            
        except Exception as e:
            print(f"Error actualizando observaciones: {e}")
    
    def _update_observation_label(self, label, observation):
        """Actualiza un label de observación con colores apropiados."""
        text, color = observation
        # Mantener fondo blanco/neutro y solo cambiar el color del texto
        label.config(text=text, fg=color, bg="white")

    def on_unit_checkbox_toggle(self, var_chk, entry_km, entry_ap, entry_po, lbl_obs_km, lbl_obs_ap, lbl_obs_po):
        """Maneja el cambio de estado del checkbox de una unidad."""
        # Actualizar contadores
        self.actualizar_contadores()
        
        # Forzar actualización del resaltado de la fila
        for fila_data in self.view.get_fila_widgets_data():
            if (fila_data['entry_km'] == entry_km and 
                fila_data['entry_ap'] == entry_ap and 
                fila_data['entry_po'] == entry_po):
                self.view.update_row_highlighting(fila_data)
                break

    def actualizar_contadores(self):
        """Actualiza contadores con optimización."""
        pickup_count = 0
        autos_count = 0
        
        for fila_data in self.view.get_fila_widgets_data():
            if fila_data['var_chk'].get() and fila_data['alias'] in self.view.unidades_mostradas:
                alias = fila_data['alias']
                if self._is_camioneta(alias):
                    pickup_count += 1
                elif self._is_auto(alias):
                    autos_count += 1
        
        total_pickup = len(self.model.CAMIONETAS)
        total_autos = len(self.model.AUTOS)
        
        self.view.update_counters(pickup_count, total_pickup, autos_count, total_autos)

    def _actualizar_turno_logic(self):
        """Lógica optimizada para actualizar turno basado en hora actual."""
        try:
            # Obtener hora actual de forma asíncrona si es la primera vez
            if self.first_turno_update:
                def get_time_and_update():
                    hora_actual = self.time_service.get_network_time()
                    self.view.root.after(0, lambda: self._set_turno_from_time(hora_actual))
                
                self.thread_pool.submit(get_time_and_update)
                self.first_turno_update = False
            else:
                # Usar hora almacenada en caché
                if self.time_service.last_known_time:
                    self._set_turno_from_time(self.time_service.last_known_time)
                else:
                    # Fallback a hora local
                    hora_local = datetime.now(self.time_service.timezone)
                    self._set_turno_from_time(hora_local)
                    
        except Exception as e:
            print(f"Error actualizando turno: {e}")
            # Fallback a hora local
            hora_local = datetime.now(self.time_service.timezone)
            self._set_turno_from_time(hora_local)
    
    def _set_turno_from_time(self, hora_actual):
        try:
            hora = hora_actual.hour
            if hora >= 22 or hora < 6:
                turno = "NOCHE"
            elif hora >= 6 and hora < 14:
                turno = "DÍA"
            elif hora >= 14 and hora < 22:
                turno = "TARDE"
            else:
                turno = "TARDE"
            self.view.turno_var.set(turno)
        except Exception as e:
            print(f"Error estableciendo turno: {e}")


    def refresh_turno(self):
        """Refreshes the current shift based on the known system time."""
        self._actualizar_turno_logic()
        self.view.update_status("⏰ Turno actualizado según hora actual", "green")

     
    def actualizar_reloj(self):
        """Actualiza el reloj con tiempo de red optimizado."""
        try:
            if self.time_service.last_known_time:
                tiempo_actual = self.time_service.last_known_time + timedelta(
                    seconds=time.time() - (self.time_service.last_ntp_update or 0)
                )
            else:
                tiempo_actual = datetime.now(self.time_service.timezone)
            
            tiempo_str = tiempo_actual.strftime("%H:%M:%S")
            fecha_str = tiempo_actual.strftime("%d/%m/%Y")
            
            self.view.update_reloj(f"{tiempo_str} | {fecha_str}")
            
            # Programar siguiente actualización
            self.view.root.after(1000, self.actualizar_reloj)
            
        except Exception as e:
            print(f"Error actualizando reloj: {e}")
            # Fallback con hora local
            tiempo_local = datetime.now()
            tiempo_str = tiempo_local.strftime("%H:%M:%S | %d/%m/%Y")
            self.view.update_reloj(tiempo_str)
            self.view.root.after(1000, self.actualizar_reloj)

    def editar_datos(self):
        """Habilita el modo de edición con feedback optimizado."""
        self.editing_mode = True
        self.view.set_editing_mode(True)
        self.view.update_status("✏️ Modo de edición activado - Puede modificar los datos", "blue")
        
        # Reproducir sonido de confirmación (solo en Windows)
        try:
            winsound.MessageBeep(winsound.MB_OK)
        except:
            pass

    def guardar_datos(self):
        """Guarda datos con validación optimizada y backup automático."""
        try:
            # Validar datos antes de guardar
            if not self._validate_all_data():
                return
            
            units_data = self.view.get_unit_selection_data()
            turno_actual = self.view.get_turno_var()
            
            if not units_data:
                self.view.show_message("Advertencia", "No hay unidades seleccionadas para guardar.", "warning")
                return
            
            # Usar el nuevo helper asíncrono para guardar
            def save_op():
                filtro_activo = self.view.get_filtro_var()
                return self.model.guardar_registro(units_data, turno_actual, filtro_activo)
            
            self.view.update_status("💾 Guardando datos (Local + Nube)...", "blue")
            self._run_task_async(
                save_op,
                on_success=self._handle_save_result,
                loading_msg="Guardando datos en local y nube..."
            )
            
        except Exception as e:
            self.view.show_message("Error", f"Error al guardar datos: {str(e)}", "error")
            self.view.update_status("❌ Error al guardar datos", "red")
    
    def _validate_all_data(self):
        """Valida todos los datos antes de guardar."""
        units_data = self.view.get_unit_selection_data()
        
        if not units_data:
            self.view.show_message("Advertencia", "No hay unidades seleccionadas.", "warning")
            return False
        
        # Validar que al menos una unidad tenga datos
        has_data = any(unit['km'] or unit['ap'] or unit['po'] != '0' for unit in units_data)
        
        if not has_data:
            result = self.view.show_message("Confirmación", 
                "No se han ingresado datos en las unidades seleccionadas. ¿Desea continuar?", 
                "askyesno")
            return result
        
        return True
    
    def _handle_save_result(self, success):
        """Maneja el resultado de la operación de guardado."""
        if success:
            self.editing_mode = False
            self.view.set_editing_mode(False)
            self.view.update_status("✅ Datos guardados exitosamente", "green")
            
            # Sonido de éxito
            try:
                winsound.MessageBeep(winsound.MB_OK)
            except:
                pass
        else:
            self.view.update_status("❌ Error al guardar datos", "red")
            try:
                winsound.MessageBeep(winsound.MB_ICONHAND)
            except:
                pass

    def limpiar_formulario(self, skip_confirm=False):
        """Limpia el formulario con confirmación inteligente."""
        if self.editing_mode:
            # Verificar si hay datos para limpiar
            has_data = any(
                fila['entry_km'].get() or fila['entry_ap'].get() or fila['entry_po'].get() != '0'
                for fila in self.view.get_fila_widgets_data()
                if fila['var_chk'].get()
            )
            
            if has_data:
                if not skip_confirm:
                    result = self.view.show_message("Confirmación", 
                        "¿Está seguro de que desea limpiar todos los datos ingresados?", 
                        "askyesno")
                    if not result:
                        return
        
        self.view.clear_form()
        self.actualizar_contadores()
        self.view.update_status("🧹 Formulario limpiado", "green")
        
        # Sonido de confirmación
        try:
            winsound.MessageBeep(winsound.MB_OK)
        except:
            pass

    def capturar_pantalla_completa(self):
        """Captura la pantalla completa de la aplicación usando la API de Windows."""
        if not self.editing_mode:
            self.view.show_message("⚠️ Advertencia", "🖱️ Debes hacer clic en '✏️ EDITAR' antes de capturar la pantalla.", "warning")
            return
        
        # Reutilizar la validación de campos existente
        if not self.validar_campos():
            self.view.show_message("⚠️ Validación", "Complete todos los campos requeridos antes de capturar la pantalla.", "warning")
            return
        
        try:
            self.view.update_status("📸 Capturando pantalla...", "blue")
            import win32gui
            import win32ui
            import win32con
            from PIL import Image
            
            # Obtener el handle de la ventana
            hwnd = self.view.root.winfo_id()
            
            # Obtener las dimensiones de la ventana
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            # Crear un contexto de dispositivo
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            
            # Crear un bitmap para guardar la imagen
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            # Copiar la pantalla al bitmap
            result = saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
            
            if not result:
                # Convertir el bitmap a una imagen PIL
                bmpinfo = saveBitMap.GetInfo()
                bmpstr = saveBitMap.GetBitmapBits(True)
                screenshot = Image.frombuffer(
                    'RGB',
                    (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                    bmpstr, 'raw', 'BGRX', 0, 1)
                
                # Guardar la imagen
                img_folder = self.model.get_img_folder()
                try:
                    os.makedirs(img_folder, exist_ok=True)
                except Exception as e:
                    self.view.show_message("Error", f"No se pudo crear la carpeta de imágenes: {str(e)}", "error")
                    return
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(img_folder, f"captura_{timestamp}.png")
                
                try:
                    screenshot.save(filename, "PNG")
                except Exception as e:
                    self.view.show_message("Error", f"No se pudo guardar la captura: {str(e)}", "error")
                    return
                
                # NUEVA FUNCIONALIDAD: Copiar al portapapeles
                try:
                    self._copy_report_image_to_clipboard(screenshot)
                except Exception as e:
                    # Si falla la copia al portapapeles, continuar pero mostrar advertencia
                    print(f"Advertencia: No se pudo copiar al portapapeles: {e}")
                else:
                    # La copia al portapapeles fue exitosa
                    pass
                   
                                               
                self.view.update_status(f"Captura guardada en {filename}")
                self.view.show_message_with_link("✅ Éxito", 
                                     "Captura de pantalla completada", 
                                     filename, "info")
            else:
                raise RuntimeError("Error al capturar la pantalla")
                
            # Limpiar recursos
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)
            
        except Exception as e:
            self.view.show_message("Error", f"No se pudo capturar la pantalla: {str(e)}", "error")
    
    def _copy_report_image_to_clipboard(self, img):
        """Copia una imagen al portapapeles."""
        if not (Image and win32clipboard):
            return
            
        import io
        
        output = io.BytesIO()
        img.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]  # El encabezado BMP no es necesario
        output.close()
        
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()

    def validar_campos(self):
        """
        Valida que los campos requeridos estén completos para las unidades seleccionadas.
        """
        if self.view.get_turno_var() in ["", "SELECCIONAR..."]:
            self.view.show_message(
                "⚠️ Validación",
                "⏰ Seleccione un turno principal antes de continuar.",
                "warning")

            return False

        selected_units_data = self.view.get_unit_selection_data()
        if not selected_units_data:
            self.view.show_message(
                "⚠️ Validación",
                "🗂️ Debe seleccionar al menos una unidad para continuar.",
                "warning")

            return False

        for data in selected_units_data:
            alias = data['alias']
            km = data['km']
            ap = data['ap']
            po = data['po']
            turnos = data['turnos_seleccionados']

            if not all([km.strip(), ap.strip()]):
                self.view.show_message(
                    "⚠️ Validación de Campos",
                    f"📝 Complete todos los campos requeridos (KM, AP) para la unidad 📂 {alias}.",
                    "warning")

                return False
            if not turnos:
                self.view.show_message(
                    "⚠️ Validación",
                    f"⏰ Debe seleccionar al menos un turno para 📂 {alias}.",
                    "warning")

                return False


        return True

    def cargar_ultimo_registro(self):
        """Carga el último registro guardado con feedback mejorado y diálogo de espera."""
        try:
            self.view.update_status("⏮️ Sincronizando con base de datos...", "blue")
            
            def load_op():
                # Limpiar la caché del último registro antes de cargar
                self.model.cache.delete("last_record")
                return self.model.cargar_ultimo_registro()
            
            self._run_task_async(
                load_op,
                on_success=self._handle_load_result_complete,
                loading_msg="Sincronizando con la nube y local..."
            )
            
        except Exception as e:
            self.view.show_message("Error", f"Error al iniciar carga: {str(e)}", "error")
            self.view.update_status("❌ Error de comunicación", "red")

    def _handle_load_result_complete(self, ultimo_registro):
        """Cierra el diálogo y procesa el resultado de la carga."""
        if hasattr(self, '_loading_dialog'):
            self._loading_dialog.close()
            del self._loading_dialog
            
        self._handle_load_result(ultimo_registro)
    
    def _handle_load_result(self, ultimo_registro):
        """Maneja el resultado de la carga del último registro."""
        if ultimo_registro:
            self._apply_loaded_data(ultimo_registro)
            self.view.update_status("✅ Último registro cargado exitosamente", "green")
            
            # Sonido de éxito
            try:
                winsound.MessageBeep(winsound.MB_OK)
            except:
                pass
        else:
            self.view.show_message("Información", "No se encontraron registros anteriores.", "info")
            self.view.update_status("ℹ️ No hay registros anteriores", "orange")
    
    def _apply_loaded_data(self, registro_data):
        """Aplica los datos cargados a la interfaz de usuario."""
        if not registro_data or 'units_data' not in registro_data:
            self.view.show_message("Error", "Formato de datos inválido", "error")
            return

        # LIMPIAR FORMULARIO ANTES DE CARGAR (forzar limpieza total)
        self.limpiar_formulario(skip_confirm=True)

        # Obtener el turno del registro
        turno_registro = registro_data.get('turno', 'NOCHE')
        
        # Aplicar datos a cada unidad
        for unit in registro_data['units_data']:
            alias = unit['alias']
            
            # Buscar la fila correspondiente
            for fila_data in self.view.fila_widgets_data:
                if fila_data['alias'] == alias:
                    # Set the values
                    fila_data['entry_km'].delete(0, tk.END)
                    fila_data['entry_km'].insert(0, unit['km'])
                    fila_data['entry_ap'].delete(0, tk.END)
                    fila_data['entry_ap'].insert(0, unit['ap'])
                    fila_data['entry_po'].delete(0, tk.END)
                    fila_data['entry_po'].insert(0, unit['po'])
                    
                    # Set the turnos checkboxes - manejar caso donde no existe 'turnos_seleccionados'
                    turnos_seleccionados = unit.get('turnos_seleccionados', [turno_registro])
                    for turno_name, var in fila_data['check_vars_turnos'].items():
                        var.set(turno_name in turnos_seleccionados)
                    
                    # Set jurisdiction / zona if available
                    zona_val = unit.get('zona') or unit.get('jurisdiccion', '')
                    if str(zona_val).upper() == "T.ALTA":
                        zona_val = "SUR"
                    elif str(zona_val).upper() == "SECTORIAL":
                        zona_val = "CENTRO"

                    if 'var_zona' in fila_data:
                        fila_data['var_zona'].set(str(zona_val).upper() if zona_val else "")
                    if 'var_jurisdiccion' in fila_data:
                        fila_data['var_jurisdiccion'].set(unit.get('jurisdiccion', zona_val))
                    
                    # Ensure the checkbox is checked
                    fila_data['var_chk'].set(True)
                    
                    # Update observations
                    self.actualizar_observaciones_gui(
                        fila_data['entry_km'], fila_data['entry_ap'], fila_data['entry_po'],
                        fila_data['lbl_obs_km'], fila_data['lbl_obs_ap'], fila_data['lbl_obs_po']
                    )
                    
                    # Update row highlighting
                    self.view.update_row_highlighting(fila_data)
                    
                    break  # No need to check other rows
        
        # Obtener las unidades del último registro para aplicar filtro MANUAL
        unidades_ultimo_registro = [unit['alias'] for unit in registro_data['units_data']]
        
        # Aplicar automáticamente el filtro MANUAL con las unidades del último registro
        # SIN abrir la ventana de selección manual
        self.view.filtro_var.set('MANUAL')
        
        # Actualizar la vista con el filtro MANUAL aplicado directamente
        # sin llamar a show_unit_selection_window
        self.view.update_unit_display(
            units_to_display=unidades_ultimo_registro,
            filter_type='MANUAL',
            is_editing_mode=self.editing_mode,
            selected_units_by_checkbox=unidades_ultimo_registro
        )
        
        # Ensure the UI is fully updated with editing mode enabled
        self.view.set_editing_mode(True)
        
        # Actualizar contadores y estado
        self.actualizar_contadores()
        self.view.update_status("✅ Último registro cargado con filtro MANUAL aplicado", "green")

    def _is_camioneta(self, alias: str) -> bool:
        """Determina si un alias pertenece a una camioneta."""
        if not alias:
            return False
        codigo = self.model.ALIAS_UNIDADES.get(alias, '')
        if not codigo and ' / ' in alias:
            codigo = alias.split(' / ')[1].split(';')[0].strip()
        if not codigo:
            for part in alias.replace(';', ' ').split():
                if part in self.model.CAMIONETAS:
                    return True
        if codigo in self.model.CAMIONETAS:
            return True
        if alias in self.model.CAMIONETAS:
            return True
        if '🚙' in alias or 'PICKUP' in alias.upper():
            return True
        return False

    def _is_auto(self, alias: str) -> bool:
        """Determina si un alias pertenece a un auto sedán."""
        if not alias:
            return False
        codigo = self.model.ALIAS_UNIDADES.get(alias, '')
        if not codigo and ' / ' in alias:
            codigo = alias.split(' / ')[1].split(';')[0].strip()
        if not codigo:
            for part in alias.replace(';', ' ').split():
                if part in self.model.AUTOS:
                    return True
        if codigo in self.model.AUTOS:
            return True
        if alias in self.model.AUTOS:
            return True
        if '🚘' in alias or 'AUTO' in alias.upper() or 'SEDAN' in alias.upper():
            return True
        return False

    def imprimir_reporte(self):
        """Genera y abre el reporte en formato JPG y copia resumen al portapapeles."""
        selected_units_data = self.view.get_unit_selection_data()
        turno_actual = self.view.get_turno_var()

        if not selected_units_data:
            self.view.show_message("Advertencia", "No hay unidades seleccionadas para generar el reporte.", "warning")
            return

        def generate_report_task():
            # Ejecutar generación pesada (Pillow/PDF) en segundo plano
            success, file_path = self.model.generar_reporte_jpg(selected_units_data, turno_actual)
            return success, file_path

        def on_report_finished(result):
            success, file_path = result
            if not success:
                self.view.show_message("Error", f"No se pudo generar el reporte:\n{file_path}", "error")
                return

            try:
                # 1. Copiar la imagen al portapapeles
                copied_img = False
                try:
                    if Image and win32clipboard:
                        img = Image.open(file_path)
                        self._copy_report_image_to_clipboard(img)
                        copied_img = True
                except Exception as e:
                    print(f"Error copiando imagen al portapapeles: {e}")
                
                if copied_img:
                    msg_exito = (f"🖼️ La imagen del reporte se copió al portapapeles y se guardó en:\n📁 {file_path}\n"
                                 "Ya puedes pegarla (Ctrl+V) en WhatsApp.")
                else:
                    msg_exito = (f"🖼️ Reporte guardado en:\n📁 {file_path}\n"
                                 "Ya puedes continuar con la configuración del reporte.")
                
                # Mostrar primer diálogo informando que la imagen está lista
                # La ejecución se pausa aquí hasta que el usuario haga clic en 'Aceptar'
                self.view.show_message("✅ Éxito", msg_exito, "info")
                
                # 2. AL ACEPTAR el primer diálogo, mostrar la ventana para configurar fuente de datos y nota
                fuente_datos, nota = self._mostrar_ventana_fuente_y_nota()
                
                # 3. Generar la plantilla de texto contando únicamente las unidades operativas en el turno actual
                resumen = self._generar_contenido_portapapeles(selected_units_data, turno_actual, fuente_datos, nota)
                
                # 4. Copiar texto al portapapeles
                pyperclip.copy(resumen)
                
                # 5. Mostrar ventana informando que el texto se copió al portapapeles
                self.view.show_message("📎 Texto copiado", 
                                     "📄 El texto del reporte se ha copiado al portapapeles.\n\n"
                                     "🚀 Ahora puedes pegarlo (Ctrl+V) en WhatsApp Web después de pegar la imagen.", 
                                     "info")
            except Exception as e:
                self.view.show_message("Error", f"No se pudo procesar el reporte: {str(e)}", "error")

        self.view.update_status("🎨 Generando reporte...", "blue")
        self._run_task_async(generate_report_task, on_success=on_report_finished, loading_msg="Generando imagen del reporte...")

    def _generar_contenido_portapapeles(self, unidades_data, turno_actual, fuente_datos="SIPCOP-M", nota=""):
        ahora = datetime.now()
        hora_str = ahora.strftime('%H:%M')
        fecha_str = ahora.strftime('%Y-%m-%d')
        equipo_str = os.getenv('COMPUTERNAME', 'Sistema').upper()
        
        # Función para normalizar turnos (ignora tildes, mayúsculas/minúsculas y espacios)
        def normalize_shift(s: str) -> str:
            if not s:
                return ""
            import unicodedata
            return unicodedata.normalize('NFKD', str(s)).encode('ASCII', 'ignore').decode('utf-8').strip().upper()
            
        current_shift_norm = normalize_shift(turno_actual)
        
        # Obtener contadores de unidades (solo las que están operando en el turno actual)
        count_pickup = 0
        count_autos = 0
        
        for data in unidades_data:
            turnos_unidad = [normalize_shift(t) for t in data.get('turnos_seleccionados', [])]
            # Solo contar unidades que tienen marcado el turno actual
            if current_shift_norm in turnos_unidad:
                alias = data.get('alias', '')
                if self._is_camioneta(alias):
                    count_pickup += 1
                elif self._is_auto(alias):
                    count_autos += 1
        
        # Generar el contenido con el formato exacto solicitado
        contenido = [
            f"📊 REPORTE DE TURNO – {turno_actual}",
            f"🕒 {hora_str} | 📅 {fecha_str}",
            " ⚙️🚗 Unidades en operación:",
            f"🔹 🚙 Camionetas [{count_pickup}]",
            f"🔹 🚘 Autos Sedán [{count_autos}]",
            f"📡 Fuente: {fuente_datos}",
            "📝 Novedad:",
            nota.strip() if (nota and nota.strip()) else "Sin novedades.",
            f"👤 Registro: {equipo_str}"
        ]
        
        return "\n".join(contenido)

    def _mostrar_ventana_fuente_y_nota(self):
        """Muestra ventana emergente para seleccionar fuente de datos y agregar nota.
        Retorna:
            tuple: (fuente_datos, nota) donde nota puede ser string vacío
        """
        ventana = tk.Toplevel(self.view.root)
        ventana.title("Configuración de Reporte")
        ventana.geometry("500x450")
        ventana.resizable(False, False)
        ventana.attributes('-topmost', True)
        ventana.configure(bg=self.view.COLOR_FONDO)
        
        # Centrar sobre la ventana principal
        ventana.transient(self.view.root)
        ventana.update_idletasks()
        try:
            x = self.view.root.winfo_x() + (self.view.root.winfo_width() // 2) - 250
            y = self.view.root.winfo_y() + (self.view.root.winfo_height() // 2) - 225
            ventana.geometry(f"500x450+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass
        
        # Variable para los radio buttons
        fuente_var = tk.StringVar(value="SIPCOP-M")
        
        # Frame para selección de fuente
        fuente_frame = tk.Frame(ventana, bg=self.view.COLOR_FONDO, padx=15, pady=15)
        fuente_frame.pack(fill=tk.X)
        
        tk.Label(fuente_frame, text="📡 Fuente de datos:", 
                font=self.view.font_boton, bg=self.view.COLOR_FONDO).pack(anchor="w")
        
        # Frame para los radio buttons en horizontal
        radio_frame = tk.Frame(fuente_frame, bg=self.view.COLOR_FONDO)
        radio_frame.pack(fill=tk.X, pady=8)
        
        # Radio buttons en horizontal con espaciado
        ttk.Radiobutton(radio_frame, text="🗺️ SIPCOP-M", variable=fuente_var, 
                        value="SIPCOP-M", style='Toolbutton').pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(radio_frame, text="🌍 Wialon", variable=fuente_var, 
                        value="Wialon", style='Toolbutton').pack(side=tk.LEFT, padx=10)
        
        # Frame para nota
        nota_frame = tk.Frame(ventana, bg=self.view.COLOR_FONDO, padx=15, pady=5)
        nota_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(nota_frame, text="📝 Nota adicional (opcional):", 
                font=self.view.font_boton, bg=self.view.COLOR_FONDO).pack(anchor="w")
        
        text_nota = tk.Text(nota_frame, height=8, width=40, wrap=tk.WORD,
                            font=self.view.font_base, relief=tk.SOLID, bd=1)
        text_nota.pack(fill=tk.BOTH, expand=True, pady=8)
        text_nota.focus_set()
        
        # Variables para retornar
        resultado = {"fuente": "SIPCOP-M", "nota": ""}
        
        def confirmar():
            resultado["fuente"] = fuente_var.get()
            resultado["nota"] = text_nota.get("1.0", tk.END).strip()
            ventana.destroy()
        
        btn_frame = tk.Frame(ventana, bg=self.view.COLOR_FONDO)
        btn_frame.pack(pady=15)
        
        # Botón Confirmar
        btn_confirmar = ttk.Button(btn_frame, text="Confirmar", command=confirmar,
                                   style='Accent.TButton')
        btn_confirmar.pack(pady=5)
        
        # Atajo Ctrl+Enter para confirmar
        ventana.bind('<Control-Return>', lambda e: confirmar())
        
        ventana.grab_set()
        self.view.root.wait_window(ventana)
        
        return resultado["fuente"], resultado["nota"]

    def megafono(self):
        """Abre ventana de megáfono con gestión de ventanas mejorada."""
        try:
            abrir_ventana_megafonos(self.view.root)
            self.view.update_status("📢 Megáfono activado", "green")
        except Exception as e:
            self.view.show_message("Error", f"Error abriendo megáfono: {str(e)}", "error")

    def open_wialon(self):
        """Abre directamente la URL de Wialon Hosting."""
        def open_link():
            try:
                url = self.model.WIALON_CONFIG.get("url_monitor", "https://hosting.wialon.us/?lang=es")
                webbrowser.open(url)
                self.view.root.after(0, lambda: self.view.update_status("🌍 Wialon abierto", "green"))
            except Exception as e:
                self.view.root.after(0, lambda: self.view.show_message(
                    "Error", f"No se pudo abrir Wialon: {str(e)}", "error"))
        
        self.thread_pool.submit(open_link)

    def open_visor_tactico(self):
        """Abre la URL del Visor Táctico."""
        def open_link():
            try:
                url = getattr(self.model, "LINK_VISOR_TACTICO", "https://visor-tacticos.vercel.app/")
                webbrowser.open(url)
                self.view.root.after(0, lambda: self.view.update_status("🛰️ Visor Táctico abierto", "green"))
            except Exception as e:
                self.view.root.after(0, lambda: self.view.show_message(
                    "Error", f"No se pudo abrir Visor Táctico: {str(e)}", "error"))
        
        self.thread_pool.submit(open_link)

    def abrir_url_wialon(self):
        """Abre la URL de monitoreo de Wialon."""
        url = self.model.WIALON_CONFIG.get("url_monitor", "https://hosting.wialon.us/?lang=es")
        webbrowser.open(url)
        self.view.update_status("🌍 Wialon abierto", "green")

    def consultar_km_wialon(self):
        """Consulta KM recorrido + A.P. (estacionamiento) desde Wialon para unidades seleccionadas."""
        if not self.editing_mode:
            self.view.show_message("⚠️ Advertencia", "🖱️ Debes activar '✏️ EDITAR' antes de consultar Wialon.", "warning")
            return

        units_data = self.view.get_unit_selection_data()
        if not units_data:
            self.view.show_message("⚠️ Advertencia", "No hay unidades seleccionadas.", "warning")
            return

        def ejecutar_consulta():
            import re
            from datetime import datetime, timezone, timedelta
            
            token = self.model.WIALON_CONFIG.get("token")
            if not token:
                raise ValueError("Token de Wialon no encontrado en config.json")

            api = WialonAPI(token)

            # Construir mapeo
            def limpiar_alias(a):
                limpio = re.sub(r'^[^\w0-9]+', '', a).strip()
                return " ".join(limpio.split()).upper()

            unidades_a_consultar = []
            mapping_inverso = {} 

            for unit in units_data:
                alias_original = unit['alias']
                wialon_name = self.model.WIALON_MAPPING.get(alias_original) or limpiar_alias(alias_original)
                unidades_a_consultar.append(wialon_name)
                mapping_inverso[wialon_name] = alias_original

            # ── PASO 1: KM recorrido ─────────────────────────────────────
            data_km = api.get_daily_mileage(unidades_a_consultar)

            api.logout()
            return data_km, mapping_inverso

        def on_consult_finished(result):
            data_km, mapping_inverso = result
            exito_km = 0

            for wialon_name, alias in mapping_inverso.items():
                info_km = data_km.get(wialon_name, {})

                for fila in self.view.fila_widgets_data:
                    if fila['alias'] == alias and fila['var_chk'].get():
                        if info_km:
                            self._actualizar_km_wialon(fila, info_km)
                            exito_km += 1
                        break

            self.view.update_status(f"✅ Wialon: {exito_km} KMs sincronizados", "green")

        self.view.update_status("📡 Consultando Wialon RM API...", "blue")
        self._run_task_async(
            ejecutar_consulta,
            on_success=on_consult_finished,
            loading_msg="Conectando con Wialon...\nEsto puede tardar unos segundos."
        )

    def _actualizar_campos_wialon(self, fila_widgets, data_info):
        """[Legado] Actualiza KM y JURISDICCION - redirige al nuevo método."""
        self._actualizar_km_wialon(fila_widgets, data_info)

    def _actualizar_km_wialon(self, fila_widgets, data_info):
        """Actualiza el campo KM y JURISDICCION desde datos de Wialon."""
        valor_km = data_info.get("km", 0)
        juris = data_info.get("jurisdiccion", "SECTORIAL")

        entry_km = fila_widgets['entry_km']
        entry_km.delete(0, tk.END)
        entry_km.insert(0, str(int(valor_km)))

        fila_widgets['var_jurisdiccion'].set(juris)
        entry_km.event_generate('<KeyRelease>')

    def _actualizar_ap_wialon(self, fila_widgets, data_ap):
        """Actualiza el campo A.P. con el valor calculado desde cronologías de estacionamiento."""
        ap_min = data_ap.get("ap_min", 0)
        parking_min = data_ap.get("parking_min", 0)

        entry_ap = fila_widgets['entry_ap']
        entry_ap.delete(0, tk.END)
        entry_ap.insert(0, str(ap_min))

        # Disparar validación de observaciones
        entry_ap.event_generate('<KeyRelease>')

        # Actualizar label de observación A.P. si existe
        try:
            lbl_obs_ap = fila_widgets.get('lbl_obs_ap')
            lbl_obs_km = fila_widgets.get('lbl_obs_km')
            lbl_obs_po = fila_widgets.get('lbl_obs_po')
            entry_km = fila_widgets.get('entry_km')
            entry_po = fila_widgets.get('entry_po')
            if all([lbl_obs_km, lbl_obs_ap, lbl_obs_po, entry_km, entry_po]):
                self.actualizar_observaciones_gui(
                    entry_km, entry_ap, entry_po,
                    lbl_obs_km, lbl_obs_ap, lbl_obs_po
                )
        except Exception:
            pass

    def open_sipcop(self):
        """Abre SIPCOP-M con verificación de conectividad."""
        def open_link():
            try:
                webbrowser.open(self.model.LINK_SIPCOP)
                self.view.root.after(0, lambda: self.view.update_status("🗺️ SIPCOP-M abierto", "green"))
            except Exception as e:
                self.view.root.after(0, lambda: self.view.show_message(
                    "Error", f"No se pudo abrir SIPCOP-M: {str(e)}", "error"))
        
        self.thread_pool.submit(open_link)

    def confirmar_salida(self):
        if self.editing_mode:
            has_unsaved = any(
                fila['entry_km'].get() or fila['entry_ap'].get() or fila['entry_po'].get() != '0'
                for fila in self.view.get_fila_widgets_data()
                if fila['var_chk'].get()
            )
            if has_unsaved:
                result = self.view.show_message("Confirmación", 
                    "Hay cambios sin guardar. ¿Está seguro de que desea salir?", 
                    "askyesno")
                if not result:
                    return
        
        # Cerrar ventanas secundarias con verificación
        result = self.view.show_message("Confirmar salida", 
        "¿Está seguro de cerrar la aplicación?", 
        "askyesno")
        if result:
            try:
                # Proceder con el cierre
                self.view.close_all_child_windows()
                print("Ventanas secundarias cerradas")
            except Exception as e:
                print(f"Error cerrando ventanas secundarias: {e}")
            
            # Cerrar modelo
            try:
                if hasattr(self, 'model') and self.model:
                    self.model.shutdown()
                    print("Modelo cerrado")
            except Exception as e:
                print(f"Error cerrando modelo: {e}")
            
            # Cerrar recursos del controlador
            try:
                self._cleanup_resources()
                print("Recursos del controlador limpiados")
            except Exception as e:
                print(f"Error limpiando recursos: {e}")
            
            # Cerrar Tkinter con manejo explícito
            try:
                self.view.root.quit()
                print("Tkinter quit ejecutado")
                self.view.root.destroy()
                print("Tkinter destroy ejecutado")
                
                # Forzar la liberación del bucle principal
                self.view.root.update_idletasks()
            except Exception as e:
                print(f"Error cerrando Tkinter: {e}")
            
            # Forzar salida del proceso como último recurso
            import sys
            sys.exit(0)
    
    def _cleanup_resources(self):
        """Limpia todos los recursos del controlador usando el gestor centralizado."""
        try:
            # Cerrar pool de threads
            if hasattr(self, 'thread_pool') and self.thread_pool:
                self.thread_pool.shutdown(wait=True)
                print("Pool de threads cerrado")
            
            # Limpiar cachés
            with self._cache_lock:
                self._operation_cache.clear()
                self._validation_cache.clear()
                print("Cachés del controlador limpiados")
            
            # Limpiar timer de debouncing
            if hasattr(self, '_debounce_timer') and self._debounce_timer:
                try:
                    self.view.root.after_cancel(self._debounce_timer)
                    self._debounce_timer = None
                except Exception:
                    pass
            
            # Usar el gestor centralizado de recursos
            resource_manager.cleanup_all()
            
            print("Recursos del controlador limpiados correctamente")
            
        except Exception as e:
            print(f"Error limpiando recursos: {e}")

    
    def update_view_after_operation(self):
        # Recargar datos del modelo
        self.model._cargar_unidades_desde_archivo()
        
        # Obtener el filtro actual y unidades mostradas
        filtro_actual = self.view.get_filtro_var()
        unidades_mostradas = self.model.UNIDADES_DISPONIBLES
        
        # Si el filtro es MANUAL, mantener las unidades seleccionadas
        selected_units = []
        if filtro_actual == "MANUAL":
            selected_units = [fila['alias'] for fila in self.view.fila_widgets_data 
                            if fila['var_chk'].get()]
        
        # Actualizar la vista con todos los parámetros necesarios
        self.view.update_unit_display(
            units_to_display=unidades_mostradas,
            filter_type=filtro_actual,
            is_editing_mode=self.editing_mode,
            selected_units_by_checkbox=selected_units if filtro_actual == "MANUAL" else None
        )

    def vaciar_bd_excel(self):
        if not hasattr(self, '_intentos_vaciar_bd'):
            self._intentos_vaciar_bd = 0
        if not hasattr(self, '_vaciar_bd_bloqueado'):
            self._vaciar_bd_bloqueado = False
        if self._vaciar_bd_bloqueado:
            self.view.show_message("Acceso bloqueado", "Debes esperar antes de volver a intentar.", type="warning")
            return
        
        # --- NUEVO DIÁLOGO DE CONTRASEÑA CON CHECKBOX ---
        import tkinter as tk
        from tkinter import ttk
        
        dialog = tk.Toplevel(self.view.root)
        dialog.title("🗑️ Vaciar Base de Datos")
        dialog.geometry("370x180")
        dialog.configure(bg=self.view.COLOR_FONDO)
        dialog.resizable(False, False)
        dialog.transient(self.view.root)
        dialog.grab_set()
        dialog.attributes('-topmost', True)
        
        # Centrar ventana
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f'+{x}+{y}')
        
        main_frame = tk.Frame(dialog, bg=self.view.COLOR_FONDO, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(main_frame, text="🔐 Clave para 🗑️ BD:",
            font=self.view.font_boton, bg=self.view.COLOR_FONDO, fg=self.view.COLOR_HEADER).pack(anchor="w", pady=(0, 10))

        
        pass_frame = tk.Frame(main_frame, bg=self.view.COLOR_FONDO)
        pass_frame.pack(fill=tk.X, pady=5)
        
        pass_var = tk.StringVar()
        show_pass = tk.BooleanVar(value=False)
        
        entry = ttk.Entry(pass_frame, textvariable=pass_var, show="*", width=22, font=self.view.font_base)
        entry.pack(side=tk.LEFT, padx=(0, 8))
        entry.focus_set()
        
        def toggle_password():
            entry.config(show="" if show_pass.get() else "*")
        
        check = ttk.Checkbutton(pass_frame, text="👁️", variable=show_pass, command=toggle_password)
        check.pack(side=tk.LEFT)
        
        # Botones
        btn_frame = tk.Frame(main_frame, bg=self.view.COLOR_FONDO)
        btn_frame.pack(pady=(18, 0))
        
        def on_accept():
            pwd = pass_var.get()
            dialog.destroy()
            if pwd == "password&clave":
                def operacion_vaciado():
                    # 1. Respaldar antes de borrar
                    self.model._create_excel_backup()
                    # 2. Vaciar local
                    ok_local = self.model.vaciar_excel_registros()
                    # 3. Vaciar nube
                    ok_cloud = self.model.vaciar_registros_nube()
                    return ok_local, ok_cloud
                
                def on_vaciado_finish(result):
                    ok_local, ok_cloud = result
                    if ok_local and ok_cloud:
                        self.view.show_message("✅ Éxito Total", "🧹 Ambas bases de datos (Local y Nube) han sido vaciadas.", type="info")
                    elif ok_local:
                        self.view.show_message("⚠️ Éxito Parcial", "🧹 Local vaciado, pero hubo un error en la nube.", type="warning")
                    else:
                        self.view.show_message("❌ Error", "No se pudo vaciar la base de datos.", type="error")
                    
                    self._intentos_vaciar_bd = 0
                    self.view.update_status("✨ Base de datos limpia", "green")

                self.view.update_status("🧹 Limpiando bases de datos...", "blue")
                self._run_task_async(
                    operacion_vaciado,
                    on_success=on_vaciado_finish,
                    loading_msg="Realizando limpieza profunda..."
                )
            else:
                self._intentos_vaciar_bd += 1
                self.view.show_message("Contraseña incorrecta", f"La contraseña es incorrecta. Intento {self._intentos_vaciar_bd}/3.", type="error")
                if self._intentos_vaciar_bd >= 3:
                    self._vaciar_bd_bloqueado = True
                    self.view.btn_vaciarBD.pack_forget()
                    def reactivar():
                        self._vaciar_bd_bloqueado = False
                        self._intentos_vaciar_bd = 0
                        self.view.btn_vaciarBD.pack(side=tk.LEFT, padx=5)
                    self.view.root.after(15000, reactivar)
        
        def on_cancel():
            dialog.destroy()
        
        btn_aceptar = ttk.Button(btn_frame, text="Aceptar", command=on_accept, style='Danger.TButton')
        btn_aceptar.pack(side=tk.LEFT, padx=5)
        btn_cancelar = ttk.Button(btn_frame, text="Cancelar", command=on_cancel)
        btn_cancelar.pack(side=tk.LEFT, padx=5)
        
        dialog.bind('<Return>', lambda e: on_accept())
        dialog.bind('<Escape>', lambda e: on_cancel())
        dialog.wait_window()

    def mostrar_contacto(self):
        """Abre la ventana de contacto desde el controlador."""
        self.view.mostrar_contacto()

# Alias para compatibilidad
Controller = OptimizedController
