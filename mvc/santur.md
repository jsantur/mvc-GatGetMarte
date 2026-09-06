# Lógica del Sistema de Monitoreo Serenazgo

Este documento detalla la lógica operativa detrás de las funcionalidades clave del sistema, excluyendo la opción de vaciado de base de datos.

## 🎯 Metas de Control (KM, AP, PO)

El sistema valida automáticamente el cumplimiento de objetivos operativos para cada unidad:

- **KM (Kilometraje):**
    - **Meta:** 90 KM.
    - **Lógica:** 
        - Si es ≥ 90: Muestra "✅ COMPLETO".
        - Si es > 100: Muestra "✅ COMPLETO (+X KM)" indicando el excedente.
        - Si es < 90: Muestra "❌ FALTA X KM" con el cálculo del faltante.
- **AP (Auxilio Público):**
    - **Meta:** 230 minutos.
    - **Lógica:**
        - Si es ≥ 230: Muestra "✅ COMPLETO".
        - Si es < 230: Muestra "❌ FALTA X MIN (YT)" donde Y representa los "tácticos" (bloques de 30 min) necesarios para cumplir la meta.
- **PO (Personal Operativo):**
    - **Rango:** Mínimo 3, Máximo 10.
    - **Lógica:**
        - Si es ≥ 3: Muestra "✅ COMPLETO (X P.O.)".
        - Si es < 3: Muestra "❌ FALTAN X P.O.".
        - Si es > 10: Advierte "❌ PO máximo 10".

## 📊 Conteo y Filtros de Unidades

El sistema clasifica las unidades en dos categorías principales para su monitoreo:

- **Contadores:** Se actualizan en tiempo real al seleccionar/deseleccionar unidades:
    - **Camionetas (Pickups):** Basado en una lista predefinida de unidades tipo Pickup.
    - **Autos:** Basado en una lista predefinida de unidades tipo Sedán.
- **Filtros Disponibles:**
    - **TODAS:** Muestra el listado completo de unidades registradas.
    - **PICKUP:** Filtra y muestra únicamente las camionetas.
    - **AUTOS:** Filtra y muestra únicamente los autos sedán.
    - **MANUAL:** Permite abrir una ventana de selección personalizada para elegir unidades específicas de forma manual.

## 🔍 Búsqueda y Navegación

- **Buscador:** Filtra las unidades en tiempo real mientras se escribe, buscando coincidencias en los alias de las unidades. Permite términos múltiples separados por espacios.
- **Modo Navegación:** Al presionar **Enter**, se activa un resaltado amarillo que permite desplazarse por las filas de la tabla de forma rápida.

## 🛠️ Funcionalidad de Botones

- **✏️ Editar DATOS (Alt + E):** Habilita los campos de entrada para permitir la modificación de datos. Es un requisito previo para guardar o capturar pantalla.
- **💾 Guardar (Alt + G):** Realiza una validación integral de los datos y los guarda simultáneamente en:
    1. Base de datos local (Excel/SQLite).
    2. Nube (Google Sheets).
- **🧹 LIMPIAR (Alt + L):** Borra todos los datos ingresados en el formulario actual. Solicita confirmación si detecta que hay información pendiente de guardar.
- **📸 Capturar + portapapeles (Ctrl + Shift + S):** Realiza una captura de pantalla de la aplicación y la copia al portapapeles para facilitar su envío (por ejemplo, a WhatsApp). Requiere que el modo edición esté activo.
- **🔄 Último Registro (Alt + U):** Sincroniza la aplicación con la base de datos en la nube para recuperar y mostrar la información más reciente registrada.
