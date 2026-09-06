# 📚 Manual de Usuario - Sistema de Control de Unidades (v2.1)

## 1. 📖 Introducción al Sistema

Este sistema es una aplicación avanzada de gestión y control de unidades vehiculares diseñada para el seguimiento de kilómetros, auxilio público y personal operativo del cuerpo de serenazgo de Talara.

### Novedades en Versión 2.1:
- ✅ **Sincronización en la Nube (Google Sheets)**: Los datos se guardan simultáneamente en la base de datos local y en la nube (BDMarte), permitiendo la sincronización entre múltiples equipos.
- ✅ **Panel de Gestión de Cámaras (Alt+C)**: Nueva herramienta independiente para reportar el estado de las cámaras de videovigilancia con autocompletado inteligente.
- ✅ **Control de Jurisdicción**: Posibilidad de asignar sectores específicos (Sectorial, Talara Alta) a cada unidad.
- ✅ **Multi-Turno**: Las unidades ahora pueden marcarse en múltiples turnos (Día y Noche) simultáneamente si es necesario.

---

## 2. 📝 Registro de Datos

### Paso 1: Selección de Unidades
1. **Filtros rápidos (Alt + T/P/A)**:
   - 🚓 **PICKUP**: Muestra solo camionetas.
   - 🚔 **AUTOS**: Muestra solo autos sedán.
   - 🎯 **MANUAL**: Permite seleccionar unidades específicas desde una lista personalizada.
   - 📋 **TODAS**: Muestra el parque automotor completo.

2. **Búsqueda Avanzada (Alt + B)**: Escribe el código o nombre de la unidad (ej: "H1", "H5") para encontrarla instantáneamente.

### Paso 2: Ingreso de Información
Para cada unidad seleccionada, debe completar:
- **🚔 KM (Kilómetros)**: El sistema validará automáticamente si se cumple el objetivo de 90 KM.
- **📌 A.P (Auxilio Público)**: Se valida el objetivo de 230 minutos de servicio; el sistema calcula cuántos "tácticos" restan.
- **📒 P.O (Personal Operativo)**: Número de efectivos asignados a la unidad (mínimo 3 sugerido).

### Paso 3: Configuración Detallada
- **Jurisdicción**: Seleccione en el menú desplegable el sector asignado (**SECTORIAL** o **T. ALTA**).
- **Turnos**: Marque los checkboxes correspondientes (☀️ **Día** / 🌙 **Noche**) según la operatividad de la unidad en ese momento.

### Paso 4: Guardado Seguro
- Presione **Alt + G** o haga clic en **"💾 Guardar"**.
- El sistema enviará los datos a:
  1. Base de datos local (`unidades_registro.xlsx`)
  2. Base de datos Cloud (Google Sheets - BDMarte)
  3. Historial de sesión (Caché local)

---

## 3. 📹 Gestión de Cámaras (Alt + C)

El nuevo panel de cámaras permite un reporte rápido y estandarizado:
1. **Búsqueda**: Al escribir en el buscador, el sistema usará **autocompletado nativo** para encontrar cámaras oficiales registradas.
2. **Añadir**: Presione Intro o haga clic en "Añadir" para incluir la cámara en el reporte actual.
3. **Reporte**: Una vez terminada la lista, haga clic en **"💾 GENERAR Y COPIAR"**. Esto generará un texto formateado listo para ser pegado en WhatsApp o informes oficiales.

---

## 4. ⌨️ Atajos de Teclado (Guía Rápida)

### 🎯 Navegación y Tabla:
- **Enter**: Activar modo navegación / Siguiente fila.
- **Escape**: Desactivar navegación / Salir.
- **Ctrl + 1/2/3**: Ordenar tabla por Unidad, KM o Auxilio Público.
- **Ctrl + R**: Resetear ordenamiento.

### ✏️ Acciones:
- **Alt + E**: Activar modo **EDICIÓN** (Obligatorio para modificar datos).
- **Alt + G**: **GUARDAR** datos en local y nube.
- **Alt + L**: **LIMPIAR** formulario de la unidad actual.
- **Alt + C**: Abrir panel de **CÁMARAS**.
- **Alt + U**: Cargar **ÚLTIMO REGISTRO** (Sincroniza con Google Sheets).

### 📋 Sistema y Herramientas:
- **Ctrl+Shift+P**: Reporte avanzado de unidades.
- **Ctrl+Shift+B**: Abrir archivo de **BACKUP EXCEL**.
- **Ctrl+Shift+S**: Capturar pantalla y copiar al portapapeles.
- **Alt + O**: Panel de **Ocurrencias**.
- **F1**: Ayuda de atajos rápida.
- **F2**: Este Manual de Usuario.

---

## 5. ⚠️ Recomendaciones y Soporte

- 💻 **Modo Edición**: Siempre active el modo edición antes de intentar capturar pantalla o modificar campos.
- ☁️ **Sincronización**: Si nota que los datos no aparecen en otros equipos, use **⏮️ Último Registro** para forzar una sincronización con la nube.
- 🛑 **Vaciar BD**: Use la función con precaución (Alt + D), ya que eliminará los encabezados locales (aunque se mantiene el respaldo en la nube).

### ¿Necesita ayuda adicional?
- **WhatsApp**: [Click para contactar al desarrollador](https://wa.me/51977201449)
- **Contacto Directo**: Use **Ctrl + J** dentro de la aplicación para ver la tarjeta de presentación.

---
*Manual actualizado al 05 de Abril de 2026.*
