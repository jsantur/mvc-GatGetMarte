"""
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
    print("\n📊 Probando caché de configuración...")
    config1 = model.DB_CONFIG  # Primera carga
    config2 = model.DB_CONFIG  # Segunda carga (desde caché)
    
    print("\n📊 Probando caché de unidades...")
    units_count = len(model.ALIAS_UNIDADES)
    print(f"Unidades cargadas: {units_count}")
    
    print("\n📊 Probando caché de último registro...")
    record1 = model.get_last_record_optimized()  # Desde BD
    record2 = model.get_last_record_optimized()  # Desde caché
    
    print("\n📊 Estado del caché:")
    status = model.get_cache_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Ejemplo completado exitosamente")
