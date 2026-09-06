"""
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
    print(f"\n📊 Monitoreando caché: {cache_name}")
    
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
    
    print("\n✅ Pruebas de configuración completadas")
