# 📚 Manual de Usuario - Sistema de Control de Unidades

## 1. 📖 Introducción al Sistema

### ¿Qué es este sistema?
Este sistema es una aplicación de gestión y control de unidades vehiculares diseñada para el seguimiento de kilómetros, auxilio público y otros parámetros operativos de las unidades de serenazgo.

### Características principales:
- ✅ **Gestión completa de unidades**: Pick-ups y autos sedán
- ✅ **Registro de datos**: Kilómetros, auxilio público, personal operativo
- ✅ **Sistema de turnos**: Control de turnos diurnos y nocturnos
- ✅ **Filtros inteligentes**: Búsqueda y filtrado por tipo de unidad
- ✅ **Reportes automáticos**: Generación de reportes en Excel
- ✅ **Capturas de pantalla**: Funcionalidad integrada de captura
- ✅ **Backup automático**: Respaldo de datos en Excel

---

## 2. 📝 Cómo Ingresar Datos

### Paso 1: Seleccionar Unidades
1. **Filtros disponibles**:
   - 🚓 **PICKUP**: Solo unidades tipo pickup
   - 🚔 **AUTOS**: Solo unidades tipo auto sedán
   - 🎯 **MANUAL**: Selección manual de unidades específicas
   - 📋 **TODAS**: Todas las unidades disponibles

2. **Selección manual**:
   - Marca los checkboxes de las unidades que deseas editar
   - Las unidades seleccionadas se resaltarán en verde

### Paso 2: Ingresar Información
Para cada unidad seleccionada, completa los siguientes campos:

- **🚔 KM**: Kilómetros actuales de la unidad
- **📌 A.P**: Auxilio Público (número de servicios)
- **📒 P.O**: Personal Operativo (número de personas)

### Paso 3: Configurar Turnos
- Marca los checkboxes correspondientes a los turnos:
  - ☀️ **Diurno**: 06:00 - 18:00
  - 🌙 **Nocturno**: 18:00 - 06:00

### Paso 4: Guardar Datos
- Haz clic en **"💾 Guardar"** o presiona **Alt+G**
- Los datos se guardarán en la base de datos Excel

---

## 3. 🔧 Funciones Principales

### Botones de Acción Principal:
- **✏️ Editar Datos** (Alt+E): Activa el modo de edición
- **💾 Guardar** (Alt+G): Guarda los cambios realizados
- **🧹 Limpiar** (Alt+L): Limpia los campos de las unidades seleccionadas

### Botones de Acción Secundaria:
- **📸 Capturar + Portapapeles**: Toma una captura de pantalla y la copia al portapapeles
- **⏮️ Último Registro**: Carga el último registro guardado
- **🗑️ Vaciar BD**: Vacía completamente la base de datos (¡CUIDADO!)

### Funciones del Menú:

#### 📋 SISTEMA
- **📋 Reporte de Unidades** (Ctrl+Shift+P): Genera reporte detallado
- **💾 BACKUP BD** (Ctrl+Shift+B): Abre el archivo Excel de backup

#### 🔧 HERRAMIENTAS
- **📢 Megáfono** (Ctrl+M): Activa el sistema de megáfono
- **📝 Ocurrencias** (Alt+O): Registra ocurrencias del turno
- **📷 Lista de Cámaras** (Ctrl+C): Gestiona la lista de cámaras del sistema
- **🖨️ Imprimir Reporte** (Ctrl+P): Imprime el reporte actual

#### 🌐 ENLACES
- **🌍 GeoSatelital** (Ctrl+Shift+G): Abre el sistema GeoSatelital
- **🗺️ SIPCOP-M** (Ctrl+Shift+M): Abre el sistema SIPCOP-M

#### ❓ AYUDA
- **🔧 Atajos de Teclado** (F1): Muestra todos los atajos disponibles
- **📧 Contacto** (Ctrl+J): Información de contacto del desarrollador
- **📚 Manual** (F2): Este manual de usuario

---

## 4. 📷 Lista de Cámaras

### ¿Qué es la Lista de Cámaras?
La ventana de Lista de Cámaras es una herramienta que permite gestionar y visualizar todas las cámaras disponibles en el sistema de monitoreo. Esta función facilita el acceso rápido a las cámaras de seguridad y su información asociada.

### Cómo Acceder:
- **Menú**: Herramientas → Lista de Cámaras
- **Atajo**: Ctrl+C
- **Botón**: Disponible en la barra de herramientas

### Funcionalidades Principales:

#### 📋 Visualización de Cámaras:
- **Lista completa**: Muestra todas las cámaras registradas en el sistema
- **Información detallada**: Nombre, ubicación, estado y tipo de cámara
- **Búsqueda rápida**: Filtro por nombre o ubicación de cámara
- **Ordenamiento**: Organizar por diferentes criterios

#### 🔍 Búsqueda y Filtros:
- **Barra de búsqueda**: Encuentra cámaras específicas rápidamente
- **Filtros por tipo**: Cámaras fijas, móviles, PTZ, etc.
- **Filtros por estado**: Activas, inactivas, en mantenimiento

#### ⚙️ Gestión de Cámaras:
- **Ver detalles**: Información completa de cada cámara
- **Estado de conexión**: Indicador visual del estado de la cámara
- **Acceso directo**: Enlaces rápidos a las cámaras específicas

### Interfaz de Usuario:

#### Panel Principal:
- **Lista de cámaras**: Vista principal con todas las cámaras
- **Información básica**: Nombre, ubicación, estado
- **Indicadores visuales**: Iconos de estado y tipo

#### Panel de Control:
- **Botón de búsqueda**: Activa la búsqueda de cámaras
- **Botón de actualizar**: Refresca la lista de cámaras
- **Botón de cerrar**: Cierra la ventana de cámaras

### Uso Recomendado:

#### Para Operadores:
1. **Acceso rápido**: Usa Ctrl+C para abrir la lista
2. **Búsqueda eficiente**: Escribe el nombre o ubicación de la cámara
3. **Verificación de estado**: Revisa el estado de las cámaras regularmente
4. **Acceso directo**: Haz clic en una cámara para acceder a ella

#### Para Supervisores:
1. **Monitoreo general**: Revisa el estado de todas las cámaras
2. **Identificación de problemas**: Localiza cámaras con problemas
3. **Coordinación**: Usa la información para coordinar operaciones

### Características Técnicas:
- **Actualización en tiempo real**: La lista se actualiza automáticamente
- **Conexión segura**: Acceso seguro a las cámaras del sistema
- **Interfaz intuitiva**: Diseño fácil de usar y navegar
- **Compatibilidad**: Funciona con diferentes tipos de cámaras

### Notas Importantes:
- ⚠️ **Acceso restringido**: Algunas cámaras pueden requerir permisos especiales
- ⚠️ **Conexión de red**: Requiere conexión estable a la red del sistema
- ⚠️ **Rendimiento**: El número de cámaras puede afectar el rendimiento

---

## 5. ⌨️ Atajos de Teclado

### Navegación:
- **Alt+↑/↓**: Navegar entre filas de unidades
- **Alt+B**: Enfocar barra de búsqueda
- **Enter**: Confirmar entrada en campos
- **Escape**: Cancelar o limpiar

### Acciones Rápidas:
- **Alt+E**: Editar datos
- **Alt+G**: Guardar datos
- **Alt+L**: Limpiar formulario
- **Alt+C**: Capturar pantalla
- **Ctrl+C**: Lista de Cámaras
- **Alt+U**: Último registro
- **Alt+D**: Vaciar base de datos

### Menús:
- **F1**: Ayuda de atajos
- **F2**: Manual de usuario
- **Ctrl+J**: Contacto
- **Ctrl+Q**: Salir del sistema

---

## 6. 🔍 Búsqueda y Filtros

### Barra de Búsqueda:
- Busca por número de unidad (ej: "H1", "H5")
- Búsqueda en tiempo real
- Presiona **Alt+B** para enfocar rápidamente

### Filtros por Tipo:
- **🚓 PICKUP**: Solo unidades pickup
- **🚔 AUTOS**: Solo unidades auto sedán
- **🎯 MANUAL**: Selección manual
- **📋 TODAS**: Todas las unidades

### Ordenamiento:
- Haz clic en los encabezados de columna para ordenar
- **🚦 Unidad**: Ordena por número de unidad
- **🚔 KM**: Ordena por kilómetros
- **📌 A.P**: Ordena por auxilio público

---

## 7. 📊 Reportes y Exportación

### Reporte de Unidades:
- Genera reporte detallado en Excel
- Incluye estadísticas por turno
- Datos filtrados según selección actual

### Capturas de Pantalla:
- Captura automática de la interfaz
- Se guarda en carpeta de reportes
- Se copia automáticamente al portapapeles

### Backup de Datos:
- Respaldo automático en Excel
- Ubicación: `unidades_registro.xlsx`
- Acceso directo desde menú Sistema

---

## 8. ⚠️ Recomendaciones

### Buenas Prácticas:
1. **Siempre verifica** los datos antes de guardar
2. **Usa los filtros** para trabajar con grupos específicos
3. **Haz respaldos** regularmente usando la función de backup
4. **Revisa las observaciones** que aparecen en tiempo real

### Precauciones:
- ⚠️ **Vaciar BD**: Solo usar cuando sea absolutamente necesario
- ⚠️ **Datos críticos**: Verificar antes de sobrescribir
- ⚠️ **Cierre seguro**: Usar Ctrl+Q para salir correctamente

### Optimización:
- Usa los atajos de teclado para mayor velocidad
- Mantén la aplicación actualizada
- Reporta errores al desarrollador

---

## 9. 🆘 Solución de Problemas

### Problemas Comunes:

**❓ No se guardan los datos:**
- Verifica que estés en modo edición
- Asegúrate de que las unidades estén seleccionadas
- Revisa que los campos no estén vacíos

**❓ No aparecen las unidades:**
- Verifica el filtro seleccionado
- Usa "TODAS" para ver todas las unidades
- Reinicia la aplicación si es necesario

**❓ Error al generar reporte:**
- Verifica que Excel esté instalado
- Cierra otros archivos Excel abiertos
- Revisa permisos de escritura en la carpeta

**❓ Captura no funciona:**
- Verifica que la carpeta de reportes exista
- Revisa permisos de escritura
- Reinicia la aplicación

---

## 10. 📞 Contacto y Soporte

### Información de Contacto:
- **Desarrollador**: Sistema de Control de Unidades
- **WhatsApp**: [Contactar por WhatsApp](https://wa.me/51977201449)
- **Mensaje predeterminado**: "Hola Estimado(a), quisiera información sobre el sistema que ha desarrollado."

### Soporte Técnico:
- Reporta errores con capturas de pantalla
- Incluye pasos para reproducir el problema
- Menciona la versión del sistema

### Actualizaciones:
- El sistema se actualiza regularmente
- Mantén una copia de respaldo de tus datos
- Consulta las notas de versión

---

## 11. 📋 Notas Adicionales

### Versión del Sistema:
- **Versión actual**: 2.0
- **Última actualización**: Diciembre 2024
- **Compatibilidad**: Windows 10/11

### Requisitos del Sistema:
- Windows 10 o superior
- Python 3.8+
- Microsoft Excel (para reportes)
- Conexión a internet (para enlaces externos)

### Archivos Importantes:
- `unidades_registro.xlsx`: Base de datos principal
- `backups_excel/`: Carpeta de respaldos automáticos
- `REPORT/`: Carpeta de reportes generados
- `logs/`: Archivos de registro del sistema

---

*Este manual está diseñado para ayudarte a aprovechar al máximo las funcionalidades del sistema. Si tienes alguna pregunta o sugerencia, no dudes en contactar al desarrollador.* 