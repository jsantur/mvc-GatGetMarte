# Lógica del Sistema de Notificaciones - Serenazgo Talara

## Archivo Principal
`@d:\mvc\notificacion.py`

---

## 1. Estructura General

El sistema de notificaciones es una clase independiente `SistemaNotificaciones` que corre en un hilo separado (daemon) y verifica la hora cada minuto para mostrar recordatorios en momentos específicos.

```python
class SistemaNotificaciones:
    def __init__(self, view=None):
        self.config_file = "notificacion_config.json"
        self.log_file = "notificacion_system.log"
        self.running = False
        self.notification_thread = None
        self.ultima_notificacion = None
```

---

## 2. Turnos y Horarios de Notificación

Los turnos están definidos en el diccionario `self.turnos` (líneas 35-55):

### Turno DÍA
- **Horario:** 06:00 - 13:59
- **Notificaciones en:** 08:00, 09:00, 10:00, 11:00, 12:00
- **Frecuencia:** Cada 1 hora

### Turno TARDE
- **Horario:** 14:00 - 21:59
- **Notificaciones en:** 16:00, 17:00, 18:00, 19:00, 20:00
- **Frecuencia:** Cada 1 hora

### Turno NOCHE
- **Horario:** 22:00 - 05:59 (cruza medianoche)
- **Notificaciones en:** 00:00, 00:30, 01:00, 01:30, 02:00, 02:30, 03:00, 03:30, 04:00, 04:30, 05:00
- **Frecuencia:** Cada 30 minutos (media hora)

```python
self.turnos = {
    "DÍA": {
        "horario": (time(6, 0), time(13, 59)),
        "horas_validas": [
            time(8, 0), time(9, 0), time(10, 0), time(11, 0), time(12, 0)
        ]
    },
    "TARDE": {
        "horario": (time(14, 0), time(21, 59)),
        "horas_validas": [
            time(16, 0), time(17, 0), time(18, 0), time(19, 0), time(20, 0)
        ]
    },
    "NOCHE": {
        "horario": (time(22, 0), time(5, 59)),
        "horas_validas": [
            time(0, 0), time(0, 30), time(1, 0), time(1, 30), time(2, 0),
            time(2, 30), time(3, 0), time(3, 30), time(4, 0), time(4, 30), time(5, 0)
        ]
    }
}
```

---

## 3. Lógica de Verificación (Cada Minuto)

El método `_verificar_hora_periodicamente()` (línea 324) es el bucle principal:

```python
def _verificar_hora_periodicamente(self):
    """Hilo principal que verifica la hora cada minuto."""
    self.logger.info("Iniciando verificación periódica de hora")
    
    while self.running:
        try:
            self._procesar_notificacion_reporte()
            
            # Esperar hasta el siguiente minuto
            ahora = datetime.now()
            segundos_restantes = 60 - ahora.second
            time_module.sleep(segundos_restantes)
            
        except Exception as e:
            self.logger.error(f"Error en verificación periódica: {e}")
            time_module.sleep(60)  # Esperar 1 minuto en caso de error
```

### Flujo:
1. El hilo se ejecuta cada minuto (sincronizado al inicio de cada minuto)
2. Llama a `_procesar_notificacion_reporte()` para verificar si es hora de notificar
3. Duerme hasta el siguiente minuto

---

## 4. Procesamiento de Notificaciones

El método `_procesar_notificacion_reporte()` (línea 295) verifica si debe mostrar notificación:

```python
def _procesar_notificacion_reporte(self):
    """Procesa la notificación de reporte cuando es hora válida."""
    turno_actual = self._determinar_turno_actual()
    hora_actual = self._get_hora_actual().time()
    
    if not turno_actual:
        return
    if not self._es_hora_valida(hora_actual, turno_actual):
        return
    
    # Evitar notificaciones duplicadas en el mismo minuto
    hora_str = hora_actual.strftime("%H:%M")
    if self.ultima_notificacion == hora_str:
        return
    
    self.ultima_notificacion = hora_str
    self.logger.info(f"Mostrando notificación de reporte para turno {turno_actual} a las {hora_str}")
    
    # Mostrar messagebox con SÍ/NO
    respuesta = self._mostrar_messagebox_reporte()
    if respuesta:
        self._activar_ventana_principal()  # Usuario dijo SÍ
        self._enviar_sms_opcional()
    else:
        # Usuario seleccionó NO o no respondió
    
    # Guardar último recordatorio
    self.config["ultimo_recordatorio"] = datetime.now().isoformat()
    self._save_config()
```

### Lógica de validación:
1. Determina el turno actual basado en la hora
2. Verifica si la hora actual está en la lista de `horas_validas` del turno
3. Evita duplicados comparando con `ultima_notificacion`
4. Muestra popup con botones SÍ (verde) / NO (rojo)
5. Si el usuario presiona SÍ, abre el reporte de unidades

---

## 5. Determinación de Turno Actual

```python
def _determinar_turno_actual(self) -> Optional[str]:
    """Determina el turno actual basado en la hora del sistema."""
    ahora = self._get_hora_actual()
    hora_actual = ahora.time()
    
    for turno, info in self.turnos.items():
        inicio, fin = info["horario"]
        
        if turno == "NOCHE":
            # Caso especial para turno noche que cruza medianoche
            if hora_actual >= inicio or hora_actual <= fin:
                return turno
        else:
            if inicio <= hora_actual <= fin:
                return turno
    
    return None
```

### Caso especial NOCHE:
El turno noche cruza la medianoche (22:00 a 05:59), por eso usa la condición `or`:
```python
if hora_actual >= inicio or hora_actual <= fin:
```

---

## 6. Verificación de Hora Válida

```python
def _es_hora_valida(self, hora_actual: time, turno: str) -> bool:
    if turno not in self.turnos:
        return False
    horas_validas = self.turnos[turno]["horas_validas"]
    # Comparar solo hora y minuto, ignorando segundos y microsegundos
    return any(hora_actual.hour == h.hour and hora_actual.minute == h.minute for h in horas_validas)
```

Compara solo hora y minuto (ignora segundos).

---

## 7. Interfaz de Notificación (Popup)

El método `_mostrar_messagebox_reporte()` (línea 156) crea un popup centrado:

- **Título:** "Sistema de Reportes"
- **Texto principal:** "¡ES EL MOMENTO DEL REPORTE!" (azul oscuro)
- **Texto secundario:** "¿QUIERES TOMARLO?" (azul oscuro)
- **Botón SÍ:** Verde (#22c55e)
- **Botón NO:** Rojo (#ef4444)
- **Auto-cierre:** 30 segundos

```python
def _mostrar_messagebox_reporte(self) -> bool:
    """Muestra un popup centrado con botones SÍ y NO."""
    # ... creación de ventana tkinter ...
    popup.after(30000, cerrar_automaticamente)  # 30 seg auto-cierre
```

---

## 8. Configuración y Archivos

### notificacion_config.json
```json
{
    "notificacion_inicial_mostrada": false,
    "ultimo_recordatorio": null,
    "sms_enabled": false,
    "sms_api_key": "",
    "intervalo_minutos": 1
}
```

### notificacion_system.log
Archivo de log con timestamp de cada notificación.

---

## 9. Funciones Públicas (API)

```python
def iniciar_sistema_notificaciones(view=None):
    """Inicia el sistema de notificaciones."""
    
def detener_sistema_notificaciones():
    """Detiene el sistema de notificaciones."""
    
def obtener_estado_sistema():
    """Retorna el estado actual del sistema."""
```

---

## 10. Resumen de Frecuencias

| Turno | Horario | Notificaciones | Frecuencia |
|-------|---------|----------------|------------|
| DÍA | 06:00 - 13:59 | 08:00, 09:00, 10:00, 11:00, 12:00 | Cada 1 hora |
| TARDE | 14:00 - 21:59 | 16:00, 17:00, 18:00, 19:00, 20:00 | Cada 1 hora |
| NOCHE | 22:00 - 05:59 | 00:00, 00:30, 01:00, 01:30, 02:00, 02:30, 03:00, 03:30, 04:00, 04:30, 05:00 | Cada 30 min |

---

## Archivos Relacionados

| Archivo | Propósito |
|---------|-----------|
| `d:\mvc\notificacion.py` | Sistema de notificaciones completo |
| `d:\mvc\notificacion_config.json` | Configuración persistente |
| `d:\mvc\notificacion_system.log` | Log de eventos |
| `d:\mvc\report_ocurrencias.py` | ToastNotification (importado) |
| `d:\mvc\utils.py` | UI_CONSTANTS (importado) |
