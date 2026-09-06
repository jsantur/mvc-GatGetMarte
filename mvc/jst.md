# Lógica de "IMPRIMIR REPORTE" - Sistema Serenazgo

## 1. Flujo Principal de `imprimir_reporte()`

Ubicación: `@d:\mvc\controller.py:910`

```python
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
            if Image and win32clipboard:
                img = Image.open(file_path)
                self._copy_report_image_to_clipboard(img)
                
                self.view.show_message("✅ Éxito", 
                                     f"🖼️ La imagen del reporte se copió al portapapeles y se guardó en:\n📁 {file_path}\n"
                                     "Ya puedes pegarla (Ctrl+V) en WhatsApp.", "info")
                
                # 2. Copiar texto con un pequeño delay
                self.view.root.after(1000, lambda: self._copy_text_after_delay(selected_units_data, turno_actual))
            else:
                self.view.show_message("✅ Éxito", f"🖼️ Reporte guardado en:\n📁 {file_path}", "info")
        except Exception as e:
            self.view.show_message("Error", f"No se pudo copiar el reporte: {str(e)}", "error")

    self.view.update_status("🎨 Generando reporte...", "blue")
    self._run_task_async(generate_report_task, on_success=on_report_finished, loading_msg="Generando imagen del reporte...")
```

---

## 2. Lógica de Copia al Portapapeles

### 2.1 Copiar Imagen (`_copy_report_image_to_clipboard`)

Ubicación: `@d:\mvc\controller.py:731`

```python
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
```

### 2.2 Copiar Texto con Delay (`_copy_text_after_delay`)

Ubicación: `@d:\mvc\controller.py:950`

```python
def _copy_text_after_delay(self, selected_units_data, turno_actual):
    """Copia el texto al portapapeles después de un retraso."""
    try:
        # 3. Copiar el texto al portapapeles
        resumen = self._generar_contenido_portapapeles(selected_units_data, turno_actual)
        pyperclip.copy(resumen)
        
        # Mostrar mensaje informativo sobre el texto
        self.view.show_message("📎 Texto copiado", 
                             "📄 El texto del reporte se ha copiado al portapapeles.\n\n"
                             "🚀 Ahora puedes pegarlo (Ctrl+V) en WhatsApp Web después de pegar la imagen.", 
                             "info")
    except Exception as e:
        self.view.show_message("Error", f"No se pudo copiar el texto al portapapeles: {str(e)}", "warning")
```

---

## 3. Generación del Contenido de Portapapeles (`_generar_contenido_portapapeles`)

Ubicación: `@d:\mvc\controller.py:965`

```python
def _generar_contenido_portapapeles(self, unidades_data, turno_actual):
    # Mostrar ventana interactiva para fuente y nota
    fuente_datos, nota = self._mostrar_ventana_fuente_y_nota()
    
    ahora = datetime.now()
    hora_str = ahora.strftime('%H:%M')
    fecha_str = ahora.strftime('%Y-%m-%d')
    equipo_str = os.getenv('COMPUTERNAME', 'Sistema').upper()
    
    # Obtener contadores de unidades (solo las que están de turno en el momento de imprimir)
    count_pickup = 0
    count_autos = 0
    _, alias_unidades, camionetas, autos = self.model.get_unit_info()
    
    for data in unidades_data:
        # Solo contar unidades que tienen marcado el turno actual
        if turno_actual in data.get('turnos_seleccionados', []):
            unidad_real = alias_unidades.get(data['alias'], data['alias'])
            if unidad_real in camionetas:
                count_pickup += 1
            elif unidad_real in autos:
                count_autos += 1
    
    # Generar el contenido con el formato compacto especificado
    contenido = [
        f"📊 REPORTE DE TURNO – {turno_actual}",
        f"🕒 {hora_str} | 📅 {fecha_str}",
        " ⚙️🚗 Unidades en operación:",
        f"🔹 🚙 Camionetas [{count_pickup}]",
        f"🔹 🚘 Autos Sedán [{count_autos}]",
        f"📡 Fuente: {fuente_datos}",
    ]
    
    if nota:
        contenido.append("📝 Novedad:")
        contenido.append(nota)
    
    contenido.append(f"👤 Registro: {equipo_str}")
    
    return "\n".join(contenido)
```

---

## 4. Formato del SMS/Mensaje Final

El formato final copiado al portapapeles es:

```
📊 REPORTE DE TURNO – {TURNO}
🕒 {HH:MM} | 📅 {YYYY-MM-DD}
 ⚙️🚗 Unidades en operación:
🔹 🚙 Camionetas [{N}]
🔹 🚘 Autos Sedán [{N}]
📡 Fuente: {SIPCOP-M|Wialon}
📝 Novedad:
{Nota opcional del usuario}
👤 Registro: {NOMBRE_EQUIPO}
```

### Ejemplo Real:
```
📊 REPORTE DE TURNO – NOCHE
🕒 22:45 | 📅 2025-04-25
 ⚙️🚗 Unidades en operación:
🔹 🚙 Camionetas [5]
🔹 🚘 Autos Sedán [8]
📡 Fuente: SIPCOP-M
📝 Novedad:
Unidad H3 presentó falla mecánica
👤 Registro: SISTEMA-SERENAZGO
```

---

## 5. Ventana de Configuración (`_mostrar_ventana_fuente_y_nota`)

Ubicación: `@d:\mvc\controller.py:1006`

Muestra una ventana emergente con:
- **Radiobuttons horizontales** para seleccionar fuente: `🗺 SIPCOP-M` o `🌍 Wialon`
- **Textarea** para agregar nota adicional (opcional)
- **Botón Confirmar** para continuar

Retorna: `(fuente_datos, nota)`

---

## 6. Generación del JPG (`generar_reporte_jpg`)

Ubicación: `@d:\mvc\model.py:1085`

### Características:
- **Tamaño**: A4 horizontal (3508 x 2480 px a 300 DPI)
- **Colores**: Azul oscuro (0,56,147), Naranja (237,125,49)
- **Estructura**:
  1. Logo en base64 (esquina superior izquierda)
  2. Título "TALARA"
  3. Fecha formateada (ej: "VIERNES, 25 DE ABRIL DE 2025")
  4. Texto "KM - 00:00 HRS / {hora_final} HORAS"
  5. Turno actual
  6. **Tabla CAMIONETAS PICK-UP** (si hay camionetas)
  7. **Tabla AUTOS SEDÁN** (si hay autos)

### Columnas de las Tablas:
| UNIDAD | KM | AP | PO | TURNO | JURISDICCION |
|--------|----|----|----|-------|--------------|
| 1 EUI-621 | 95 | 240 | 5 | NOCHE | SECTORIAL |

- **PO** tiene fondo amarillo `(255, 255, 153)`
- Filas con colores alternados (azul claro/blanco)
- Bordes de 2px en gris

---

## 7. Mensajes de Éxito al Usuario

### Mensaje 1 (Imagen copiada):
```
✅ Éxito
🖼️ La imagen del reporte se copió al portapapeles y se guardó en:
📁 {file_path}
Ya puedes pegarla (Ctrl+V) en WhatsApp.
```

### Mensaje 2 (Texto copiado):
```
📎 Texto copiado
📄 El texto del reporte se ha copiado al portapapeles.

🚀 Ahora puedes pegarlo (Ctrl+V) en WhatsApp Web después de pegar la imagen.
```

---

## 8. Secuencia Completa del Flujo

```
[Usuario presiona IMPRIMIR REPORTE]
           ↓
[Validar unidades seleccionadas]
           ↓
[Generar JPG en thread secundario]
           ↓
[Guardar imagen en carpeta IMG/]
           ↓
[Copiar imagen al portapapeles (CF_DIB)]
           ↓
[Mostrar mensaje de éxito #1]
           ↓
[Delay de 1000ms]
           ↓
[Mostrar ventana Fuente y Nota]
           ↓
[Generar texto del resumen]
           ↓
[Copiar texto al portapapeles (pyperclip)]
           ↓
[Mostrar mensaje de éxito #2]
           ↓
[Usuario puede pegar Ctrl+V en WhatsApp]
```

---

## Archivos Relacionados

| Archivo | Funciones Clave |
|---------|-----------------|
| `@d:\mvc\controller.py:910` | `imprimir_reporte()` |
| `@d:\mvc\controller.py:950` | `_copy_text_after_delay()` |
| `@d:\mvc\controller.py:965` | `_generar_contenido_portapapeles()` |
| `@d:\mvc\controller.py:1006` | `_mostrar_ventana_fuente_y_nota()` |
| `@d:\mvc\controller.py:731` | `_copy_report_image_to_clipboard()` |
| `@d:\mvc\model.py:1085` | `generar_reporte_jpg()` |
