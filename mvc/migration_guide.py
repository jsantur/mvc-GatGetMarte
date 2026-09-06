#!/usr/bin/env python3
"""
Guía de Migración y Script de Ayuda para el Sistema de Caché Mejorado

Este script ayuda a migrar del sistema de caché anterior al nuevo sistema mejorado,
proporcionando ejemplos prácticos y una herramienta de verificación de compatibilidad.
"""

import os
import shutil
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Agregar directorio actual al path para importaciones
sys.path.insert(0, '/workspace')

from cache import CacheManager

class CacheMigrationHelper:
    """Asistente para migración del sistema de caché."""
    
    def __init__(self):
        self.old_cache_dir = Path("cache")  # Directorio del caché anterior
        self.new_cache_dir = Path("cache_optimized")  # Directorio del nuevo caché
        self.backup_dir = Path("cache_backup")  # Respaldo antes de migración
    
    def analyze_existing_cache(self):
        """Analiza el caché existente y proporciona estadísticas."""
        print("🔍 Analizando caché existente...")
        
        if not self.old_cache_dir.exists():
            print("ℹ️  No se encontró directorio de caché existente")
            return None
        
        cache_files = list(self.old_cache_dir.glob("*.cache"))
        total_size = sum(f.stat().st_size for f in cache_files if f.exists())
        
        analysis = {
            'cache_files': len(cache_files),
            'total_size_mb': total_size / (1024 * 1024),
            'average_file_size_kb': (total_size / len(cache_files) / 1024) if cache_files else 0
        }
        
        print(f"📊 Análisis del caché existente:")
        print(f"   - Archivos de caché: {analysis['cache_files']}")
        print(f"   - Tamaño total: {analysis['total_size_mb']:.2f} MB")
        print(f"   - Tamaño promedio por archivo: {analysis['average_file_size_kb']:.2f} KB")
        
        return analysis
    
    def backup_existing_cache(self):
        """Crea respaldo del caché existente."""
        print("\n💾 Creando respaldo del caché existente...")
        
        if not self.old_cache_dir.exists():
            print("ℹ️  No hay caché existente para respaldar")
            return True
        
        try:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            
            shutil.copytree(self.old_cache_dir, self.backup_dir)
            print(f"✅ Respaldo creado en: {self.backup_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Error creando respaldo: {e}")
            return False
    
    def demonstrate_compatibility(self):
        """Demuestra que el nuevo sistema es compatible con el código existente."""
        print("\n🔄 Demostrando compatibilidad con código existente...")
        
        # Código que funciona igual en ambas versiones
        print("\n# Ejemplo 1: API básica (sin cambios)")
        print("cache = CacheManager()")
        print("cache.set('mi_clave', {'datos': 'importantes'})")
        print("resultado = cache.get('mi_clave')")
        print("cache.clear('mi_clave')")
        
        # Ejecutar ejemplo
        cache = CacheManager(cache_dir=str(self.new_cache_dir / "demo"))
        cache.set('mi_clave', {'datos': 'importantes'})
        resultado = cache.get('mi_clave')
        
        print(f"✅ Resultado obtenido: {resultado}")
        print(f"✅ Funcionamiento: {'CORRECTO' if resultado else 'ERROR'}")
        
        cache.clear()
    
    def demonstrate_new_features(self):
        """Demuestra las nuevas características del sistema."""
        print("\n🆕 Demostrando nuevas características...")
        
        cache = CacheManager(
            cache_dir=str(self.new_cache_dir / "advanced"),
            max_cache_size_mb=100,
            max_memory_cache_mb=50,
            enable_compression=True
        )
        
        # Ejemplo 1: Métricas de rendimiento
        print("\n# Ejemplo 1: Métricas de rendimiento")
        cache.set('test_data', {'mensaje': 'prueba de métricas'})
        cache.get('test_data')
        
        metrics = cache.get_metrics()
        print(f"Hit rate: {metrics.hit_rate:.1f}%")
        print(f"Operaciones SET: {metrics.sets}")
        print(f"Operaciones GET: {metrics.hits + metrics.misses}")
        
        # Ejemplo 2: Información detallada del caché
        print("\n# Ejemplo 2: Información detallada")
        info = cache.get_cache_info()
        print(f"Elementos en memoria: {info['memory_cache']['items']}")
        print(f"Tamaño en memoria: {info['memory_cache']['size_mb']:.2f} MB")
        print(f"Compresión habilitada: {info['configuration']['compression_enabled']}")
        
        # Ejemplo 3: Context manager
        print("\n# Ejemplo 3: Context manager (nuevo)")
        print("with CacheManager() as cache:")
        print("    cache.set('temp_data', data)")
        print("    # Limpieza automática al salir")
        
        with CacheManager(cache_dir=str(self.new_cache_dir / "context")) as temp_cache:
            temp_cache.set('temp_data', 'datos temporales')
            result = temp_cache.get('temp_data')
            print(f"✅ Context manager funciona: {result is not None}")
        
        cache.clear()
    
    def generate_migration_script(self):
        """Genera script de migración personalizado."""
        print("\n📝 Generando script de migración...")
        
        migration_script = '''#!/usr/bin/env python3
"""
Script de migración automática para el sistema de caché mejorado.
Generado automáticamente por CacheMigrationHelper.
"""

import os
import shutil
from pathlib import Path

def migrate_cache_system():
    """Migra del sistema de caché anterior al mejorado."""
    
    print("🚀 Iniciando migración del sistema de caché...")
    
    # 1. Respaldar caché existente
    old_cache = Path("cache")
    backup_cache = Path("cache_backup_migration")
    
    if old_cache.exists():
        print("💾 Respaldando caché existente...")
        if backup_cache.exists():
            shutil.rmtree(backup_cache)
        shutil.copytree(old_cache, backup_cache)
        print(f"✅ Respaldo creado en: {backup_cache}")
    
    # 2. Instalar nuevo archivo cache.py
    print("📦 El archivo cache.py mejorado debe estar en el directorio actual")
    
    # 3. Verificar compatibilidad
    try:
        from cache import CacheManager
        
        # Prueba básica
        test_cache = CacheManager(cache_dir="test_migration")
        test_cache.set("test", {"migración": "exitosa"})
        result = test_cache.get("test")
        test_cache.clear()
        
        if result:
            print("✅ Migración completada exitosamente")
            print("🎉 El nuevo sistema de caché está listo para usar")
            
            # Instrucciones post-migración
            print("\\n📋 Pasos siguientes:")
            print("1. No se requieren cambios en tu código existente")
            print("2. Opcionalmente, puedes aprovechar las nuevas características:")
            print("   - Métricas: cache.get_metrics()")
            print("   - Información: cache.get_cache_info()")
            print("   - Context manager: with CacheManager() as cache:")
            print("3. Monitorea el rendimiento con las nuevas métricas")
            
            return True
        else:
            print("❌ Error en verificación de migración")
            return False
            
    except ImportError as e:
        print(f"❌ Error importando nuevo sistema: {e}")
        print("Asegúrate de que el archivo cache.py esté en el directorio correcto")
        return False
    except Exception as e:
        print(f"❌ Error durante migración: {e}")
        return False

if __name__ == "__main__":
    success = migrate_cache_system()
    exit(0 if success else 1)
'''
        
        migration_file = Path("migrate_cache.py")
        with migration_file.open('w', encoding='utf-8') as f:
            f.write(migration_script)
        
        print(f"✅ Script de migración generado: {migration_file}")
        print("🔧 Ejecuta 'python migrate_cache.py' para migrar automáticamente")
    
    def create_integration_examples(self):
        """Crea ejemplos de integración para el código existente."""
        print("\n📚 Creando ejemplos de integración...")
        
        examples_dir = Path("cache_integration_examples")
        examples_dir.mkdir(exist_ok=True)
        
        # Ejemplo 1: Integración básica en Model
        model_example = '''"""
Ejemplo de integración del caché mejorado en la clase Model existente.
Este ejemplo muestra cómo adaptar el código actual para aprovechar las mejoras.
"""

from cache import CacheManager
from datetime import timedelta

class ModelWithImprovedCache:
    """Ejemplo de Model con caché mejorado integrado."""
    
    def __init__(self, cache_manager=None):
        # Configuración optimizada para la aplicación de unidades
        self.cache = cache_manager or CacheManager(
            cache_dir="cache_unidades",
            default_ttl=timedelta(hours=2),  # TTL más largo para datos estables
            max_cache_size_mb=200,           # Más espacio para unidades y configuración
            max_memory_cache_mb=50,          # Caché en memoria generoso
            enable_compression=True,         # Reducir uso de disco
            enable_integrity_check=True      # Seguridad de datos
        )
        
        # Cargar configuración con caché mejorado
        self._load_or_initialize_config()
        self._load_or_initialize_units()
    
    def _load_or_initialize_config(self):
        """Carga configuración con caché mejorado y fallback robusto."""
        cached_config = self.cache.get("db_config")
        if cached_config:
            self.DB_CONFIG = cached_config
            print("✅ Configuración cargada desde caché")
        else:
            # Configuración por defecto
            self.DB_CONFIG = {
                "host": "localhost",
                "user": "usuario", 
                "password": "password",
                "database": "unidades_db"
            }
            
            # Guardar en caché con TTL largo para configuración
            self.cache.set("db_config", self.DB_CONFIG, ttl=timedelta(hours=24))
            print("✅ Configuración inicializada y guardada en caché")
    
    def _load_or_initialize_units(self):
        """Carga datos de unidades con caché optimizado."""
        cached_units = self.cache.get("units_data")
        if cached_units:
            self.CAMIONETAS = cached_units['camionetas']
            self.AUTOS = cached_units['autos'] 
            self.ALIAS_UNIDADES = cached_units['alias']
            self.UNIDADES_DISPONIBLES = cached_units['disponibles']
            print(f"✅ {len(self.ALIAS_UNIDADES)} unidades cargadas desde caché")
        else:
            # Inicializar datos por defecto
            self._initialize_default_units()
            
            # Guardar en caché optimizado
            self._save_units_to_cache()
            print("✅ Unidades inicializadas y guardadas en caché")
    
    def _save_units_to_cache(self):
        """Guarda datos de unidades en caché con compresión automática."""
        units_data = {
            'camionetas': self.CAMIONETAS,
            'autos': self.AUTOS,
            'alias': self.ALIAS_UNIDADES,
            'disponibles': self.UNIDADES_DISPONIBLES,
            'last_updated': datetime.now().isoformat()
        }
        
        # El caché automáticamente comprimirá estos datos si son grandes
        success = self.cache.set("units_data", units_data, ttl=timedelta(hours=6))
        if success:
            print("✅ Datos de unidades actualizados en caché")
        else:
            print("⚠️  Advertencia: No se pudieron guardar datos en caché")
    
    def get_last_record_optimized(self):
        """Versión optimizada de get_last_record con caché inteligente."""
        # Verificar caché primero (acceso ultra-rápido)
        cached_data = self.cache.get("last_record")
        if cached_data:
            print("✅ Último registro obtenido desde caché")
            return cached_data
        
        # Si no está en caché, obtener de base de datos
        try:
            # Simular consulta a base de datos
            resultado = self._query_database_for_last_record()
            
            if resultado:
                # Guardar en caché con TTL corto (datos dinámicos)
                self.cache.set("last_record", resultado, ttl=timedelta(minutes=5))
                print("✅ Último registro obtenido de BD y guardado en caché")
                return resultado
            
        except Exception as e:
            print(f"❌ Error obteniendo último registro: {e}")
            
        return None
    
    def _query_database_for_last_record(self):
        """Simula consulta a base de datos."""
        # En implementación real, aquí iría la consulta SQL
        return {
            "id": 1,
            "timestamp": datetime.now().isoformat(),
            "unidad": "PATROL001",
            "estado": "ACTIVO"
        }
    
    def _initialize_default_units(self):
        """Inicializa unidades por defecto."""
        self.CAMIONETAS = {"PATROL001", "PATROL002", "PATROL003"}
        self.AUTOS = {"AUTO001", "AUTO002"}
        self.ALIAS_UNIDADES = {
            "PATROL001": "Patrulla 1",
            "PATROL002": "Patrulla 2", 
            "PATROL003": "Patrulla 3",
            "AUTO001": "Auto 1",
            "AUTO002": "Auto 2"
        }
        self.UNIDADES_DISPONIBLES = list(self.ALIAS_UNIDADES.keys())
    
    def get_cache_status(self):
        """Obtiene estado del caché para monitoreo."""
        metrics = self.cache.get_metrics()
        info = self.cache.get_cache_info()
        
        return {
            'hit_rate': f"{metrics.hit_rate:.1f}%",
            'total_operations': metrics.hits + metrics.misses,
            'memory_usage_mb': f"{info['memory_cache']['size_mb']:.2f}",
            'disk_usage_mb': f"{info['disk_cache']['size_mb']:.2f}",
            'cache_files': info['disk_cache']['files']
        }

# Ejemplo de uso
if __name__ == "__main__":
    from datetime import datetime
    
    print("🧪 Probando Model con caché mejorado...")
    
    # Crear instancia del modelo mejorado
    model = ModelWithImprovedCache()
    
    # Probar funcionalidad de caché
    print("\\n📊 Probando caché de configuración...")
    config1 = model.DB_CONFIG  # Primera carga
    config2 = model.DB_CONFIG  # Segunda carga (desde caché)
    
    print("\\n📊 Probando caché de unidades...")
    units_count = len(model.ALIAS_UNIDADES)
    print(f"Unidades cargadas: {units_count}")
    
    print("\\n📊 Probando caché de último registro...")
    record1 = model.get_last_record_optimized()  # Desde BD
    record2 = model.get_last_record_optimized()  # Desde caché
    
    print("\\n📊 Estado del caché:")
    status = model.get_cache_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    print("\\n✅ Ejemplo completado exitosamente")
'''
        
        with (examples_dir / "model_integration_example.py").open('w', encoding='utf-8') as f:
            f.write(model_example)
        
        # Ejemplo 2: Configuración optimizada por caso de uso
        config_example = '''"""
Ejemplos de configuración del caché optimizado para diferentes casos de uso.
"""

from cache import CacheManager
from datetime import timedelta

# Configuración 1: Aplicación de escritorio (uso actual)
def create_desktop_cache():
    """Configuración optimizada para aplicación de escritorio."""
    return CacheManager(
        cache_dir="cache_desktop",
        default_ttl=timedelta(hours=2),      # TTL moderado
        max_cache_size_mb=200,               # Espacio generoso
        max_memory_cache_mb=50,              # Memoria moderada
        max_memory_cache_size=500,           # Items moderados
        cleanup_interval_hours=12,           # Limpieza frecuente
        enable_compression=True,             # Ahorrar espacio
        enable_integrity_check=True          # Seguridad
    )

# Configuración 2: Servidor o aplicación de alto tráfico
def create_server_cache():
    """Configuración optimizada para servidor de alto tráfico."""
    return CacheManager(
        cache_dir="cache_server",
        default_ttl=timedelta(minutes=30),   # TTL corto para datos dinámicos
        max_cache_size_mb=1000,              # Mucho espacio
        max_memory_cache_mb=200,             # Mucha memoria
        max_memory_cache_size=2000,          # Muchos items
        cleanup_interval_hours=6,            # Limpieza muy frecuente
        enable_compression=True,             # Eficiencia crítica
        enable_integrity_check=True          # Seguridad crítica
    )

# Configuración 3: Dispositivo con recursos limitados
def create_minimal_cache():
    """Configuración optimizada para dispositivos con recursos limitados."""
    return CacheManager(
        cache_dir="cache_minimal",
        default_ttl=timedelta(hours=6),      # TTL largo para evitar recargas
        max_cache_size_mb=50,                # Espacio limitado
        max_memory_cache_mb=10,              # Memoria limitada
        max_memory_cache_size=100,           # Pocos items
        cleanup_interval_hours=24,           # Limpieza infrecuente
        enable_compression=True,             # Crítico para espacio
        enable_integrity_check=False         # Sacrificar por rendimiento
    )

# Configuración 4: Aplicación de análisis de datos
def create_analytics_cache():
    """Configuración optimizada para aplicaciones de análisis de datos."""
    return CacheManager(
        cache_dir="cache_analytics",
        default_ttl=timedelta(hours=24),     # TTL largo para datasets
        max_cache_size_mb=2000,              # Mucho espacio para datos
        max_memory_cache_mb=500,             # Mucha memoria para análisis
        max_memory_cache_size=1000,          # Items grandes
        cleanup_interval_hours=48,           # Limpieza infrecuente
        enable_compression=True,             # Crítico para datasets grandes
        enable_integrity_check=True          # Crítico para integridad de datos
    )

# Ejemplo de monitoreo de caché
def monitor_cache_performance(cache_manager, cache_name):
    """Monitorea el rendimiento de un caché específico."""
    print(f"\\n📊 Monitoreando caché: {cache_name}")
    
    metrics = cache_manager.get_metrics()
    info = cache_manager.get_cache_info()
    
    print(f"Hit Rate: {metrics.hit_rate:.1f}%")
    print(f"Operaciones totales: {metrics.hits + metrics.misses}")
    print(f"Memoria usada: {info['memory_cache']['size_mb']:.2f} MB")
    print(f"Disco usado: {info['disk_cache']['size_mb']:.2f} MB")
    print(f"Archivos en disco: {info['disk_cache']['files']}")
    print(f"Compresión: {'✅' if info['configuration']['compression_enabled'] else '❌'}")
    
    # Alertas de rendimiento
    if metrics.hit_rate < 50:
        print("⚠️  ALERTA: Hit rate bajo - considera ajustar TTL o tamaño de caché")
    if info['memory_cache']['size_mb'] > 90:
        print("⚠️  ALERTA: Uso de memoria alto - considera aumentar límite")
    if info['disk_cache']['size_mb'] > info['configuration']['max_size_mb'] * 0.9:
        print("⚠️  ALERTA: Uso de disco alto - considera limpieza manual")

if __name__ == "__main__":
    print("🧪 Probando diferentes configuraciones de caché...")
    
    # Probar configuración de escritorio
    desktop_cache = create_desktop_cache()
    desktop_cache.set("test_desktop", {"tipo": "escritorio", "datos": list(range(100))})
    monitor_cache_performance(desktop_cache, "Desktop")
    
    # Probar configuración mínima
    minimal_cache = create_minimal_cache()
    minimal_cache.set("test_minimal", {"tipo": "mínimo", "datos": list(range(10))})
    monitor_cache_performance(minimal_cache, "Minimal")
    
    print("\\n✅ Pruebas de configuración completadas")
'''
        
        with (examples_dir / "cache_configurations.py").open('w', encoding='utf-8') as f:
            f.write(config_example)
        
        print(f"✅ Ejemplos creados en: {examples_dir}")
        print("   - model_integration_example.py: Integración en clase Model")
        print("   - cache_configurations.py: Configuraciones optimizadas")
    
    def run_migration_assistant(self):
        """Ejecuta el asistente completo de migración."""
        print("🚀 Asistente de Migración del Sistema de Caché")
        print("=" * 50)
        
        # Paso 1: Análisis
        self.analyze_existing_cache()
        
        # Paso 2: Respaldo
        if not self.backup_existing_cache():
            print("❌ Error en respaldo. Migración cancelada.")
            return False
        
        # Paso 3: Demostración de compatibilidad
        self.demonstrate_compatibility()
        
        # Paso 4: Nuevas características
        self.demonstrate_new_features()
        
        # Paso 5: Script de migración
        self.generate_migration_script()
        
        # Paso 6: Ejemplos de integración
        self.create_integration_examples()
        
        print("\n🎉 Asistente de migración completado exitosamente")
        print("\n📋 Resumen de archivos generados:")
        print("   - migrate_cache.py: Script de migración automática")
        print("   - cache_integration_examples/: Ejemplos de integración")
        print("   - cache_backup/: Respaldo del caché anterior")
        
        print("\n📋 Próximos pasos:")
        print("1. Ejecuta 'python migrate_cache.py' para migrar")
        print("2. Revisa los ejemplos de integración")
        print("3. Adapta tu configuración específica según necesidades")
        print("4. Monitorea el rendimiento con las nuevas métricas")
        
        return True

def main():
    """Función principal del asistente de migración."""
    print("Sistema de Migración de Caché - Versión Mejorada")
    print("=" * 50)
    
    migration_helper = CacheMigrationHelper()
    success = migration_helper.run_migration_assistant()
    
    if success:
        print("\n✅ Migración preparada exitosamente")
        return True
    else:
        print("\n❌ Error durante la preparación de migración")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
