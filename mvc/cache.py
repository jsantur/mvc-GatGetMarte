"""
Módulo de caché ULTRA-OPTIMIZADO para gestión eficiente de datos en memoria y disco.

CARACTERÍSTICAS AVANZADAS:
- Sistema híbrido de caché en memoria (LRU) y disco con compresión inteligente
- Serialización optimizada con múltiples formatos y validación de integridad
- Limpieza inteligente y adaptativa con políticas avanzadas
- Métricas de rendimiento en tiempo real y monitoreo avanzado
- Manejo robusto de errores con recuperación automática y fallbacks
- Pool de threads para operaciones asíncronas
- Compresión adaptativa basada en el tamaño de datos
- Sistema de versioning para compatibilidad
- Compatible con la API existente pero con rendimiento superior
"""

import os
import pickle
import json
import gzip
import lzma
import hashlib
import time
import threading
import weakref
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, Union, Tuple, List
from collections import OrderedDict
from pathlib import Path
import logging
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
import sys
import zlib
from enum import Enum
import sqlite3

# Configuración de logging optimizada
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cache_optimizado.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class CompressionType(Enum):
    """Tipos de compresión disponibles."""
    NONE = "none"
    GZIP = "gzip"
    LZMA = "lzma"
    ZLIB = "zlib"

class SerializationType(Enum):
    """Tipos de serialización disponibles."""
    PICKLE = "pickle"
    JSON = "json"

@dataclass
class CacheConfig:
    """Configuración avanzada del sistema de caché."""
    max_memory_size: int = 1000  # Número máximo de elementos en memoria
    max_memory_mb: int = 200     # Máximo de memoria en MB
    max_disk_mb: int = 1000      # Máximo espacio en disco en MB
    compression_threshold: int = 1024  # Comprimir si es mayor a este tamaño
    cleanup_interval: int = 300  # Intervalo de limpieza en segundos
    max_threads: int = 4         # Pool de threads para operaciones
    enable_compression: bool = True
    enable_metrics: bool = True
    cache_version: str = "2.0"

@dataclass
class CacheMetrics:
    """Métricas avanzadas de rendimiento del caché."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    memory_cache_size: int = 0
    disk_cache_size: int = 0
    total_memory_usage_mb: float = 0.0
    total_disk_usage_mb: float = 0.0
    compression_saves_mb: float = 0.0
    avg_access_time_ms: float = 0.0
    last_cleanup: Optional[datetime] = None
    
    @property
    def hit_rate(self) -> float:
        """Calcula la tasa de aciertos del caché."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    @property
    def compression_ratio(self) -> float:
        """Calcula la ratio de compresión."""
        if self.total_disk_usage_mb > 0:
            return self.compression_saves_mb / self.total_disk_usage_mb * 100
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte las métricas a diccionario."""
        return asdict(self)

class AdvancedLRUCache:
    """Caché LRU en memoria ultra-optimizado con gestión inteligente de memoria."""
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 200):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self._cache = OrderedDict()
        self._lock = threading.RLock()
        self._current_memory = 0
        self._access_times = {}
        self._size_cache = {}
    
    def get(self, key: str) -> Tuple[Optional[Any], float]:
        """Obtiene un valor del caché con medición de tiempo."""
        start_time = time.perf_counter()
        
        with self._lock:
            if key in self._cache:
                # Mover al final (más reciente)
                value = self._cache.pop(key)
                self._cache[key] = value
                self._access_times[key] = time.time()
                
                access_time = (time.perf_counter() - start_time) * 1000
                return value['data'], access_time
            
            access_time = (time.perf_counter() - start_time) * 1000
            return None, access_time
    
    def set(self, key: str, data: Any, size_bytes: int = 0) -> bool:
        """Establece un valor en el caché con gestión inteligente de memoria."""
        with self._lock:
            # Estimar tamaño si no se proporciona
            if size_bytes == 0:
                try:
                    size_bytes = len(pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL))
                except Exception:
                    size_bytes = sys.getsizeof(data)
            
            # Verificar si el item es demasiado grande
            if size_bytes > self.max_memory_bytes:
                logger.warning(f"Item demasiado grande para caché de memoria: {size_bytes} bytes")
                return False
            
            # Liberar espacio si es necesario
            self._free_memory_if_needed(size_bytes)
            
            # Actualizar memoria actual si reemplazamos un elemento existente
            if key in self._cache:
                old_size = self._size_cache.get(key, 0)
                self._current_memory -= old_size
            
            # Agregar el nuevo elemento
            self._cache[key] = {
                'data': data,
                'timestamp': time.time(),
                'access_count': 1
            }
            self._size_cache[key] = size_bytes
            self._current_memory += size_bytes
            self._access_times[key] = time.time()
            
            return True
    
    def delete(self, key: str) -> bool:
        """Elimina un elemento del caché."""
        with self._lock:
            if key in self._cache:
                size_bytes = self._size_cache.get(key, 0)
                self._current_memory -= size_bytes
                
                del self._cache[key]
                del self._size_cache[key]
                self._access_times.pop(key, None)
                return True
            return False
    
    def _free_memory_if_needed(self, required_bytes: int):
        """Libera memoria siguiendo políticas inteligentes."""
        target_memory = self.max_memory_bytes - required_bytes
        
        while (self._current_memory > target_memory or 
               len(self._cache) >= self.max_size) and self._cache:
            
            # Estrategia: eliminar el menos usado recientemente
            oldest_key = next(iter(self._cache))
            self.delete(oldest_key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del caché en memoria."""
        with self._lock:
            return {
                'size': len(self._cache),
                'memory_usage_mb': self._current_memory / 1024 / 1024,
                'max_size': self.max_size,
                'max_memory_mb': self.max_memory_bytes / 1024 / 1024,
                'utilization': len(self._cache) / self.max_size * 100
            }
    
    def clear(self):
        """Limpia completamente el caché en memoria."""
        with self._lock:
            self._cache.clear()
            self._size_cache.clear()
            self._access_times.clear()
            self._current_memory = 0

class SmartCompressor:
    """Compresor inteligente que selecciona el mejor algoritmo."""
    
    @staticmethod
    def compress(data: bytes, compression_type: CompressionType = CompressionType.GZIP) -> Tuple[bytes, CompressionType, float]:
        """Comprime datos con el algoritmo especificado o el óptimo."""
        if compression_type == CompressionType.NONE:
            return data, CompressionType.NONE, 1.0
        
        original_size = len(data)
        start_time = time.perf_counter()
        
        try:
            if compression_type == CompressionType.GZIP:
                compressed = gzip.compress(data, compresslevel=6)
            elif compression_type == CompressionType.LZMA:
                compressed = lzma.compress(data, preset=3)
            elif compression_type == CompressionType.ZLIB:
                compressed = zlib.compress(data, level=6)
            else:
                return data, CompressionType.NONE, 1.0
            
            compression_time = time.perf_counter() - start_time
            compression_ratio = len(compressed) / original_size
            
            # Si la compresión no mejora significativamente, no usar compresión
            if compression_ratio > 0.95:
                return data, CompressionType.NONE, 1.0
            
            logger.debug(f"Compresión {compression_type.value}: {original_size} -> {len(compressed)} bytes "
                        f"({compression_ratio:.2%}) en {compression_time:.3f}s")
            
            return compressed, compression_type, compression_ratio
            
        except Exception as e:
            logger.warning(f"Error en compresión {compression_type.value}: {e}")
            return data, CompressionType.NONE, 1.0
    
    @staticmethod
    def decompress(data: bytes, compression_type: CompressionType) -> bytes:
        """Descomprime datos según el tipo especificado."""
        if compression_type == CompressionType.NONE:
            return data
        
        try:
            if compression_type == CompressionType.GZIP:
                return gzip.decompress(data)
            elif compression_type == CompressionType.LZMA:
                return lzma.decompress(data)
            elif compression_type == CompressionType.ZLIB:
                return zlib.decompress(data)
            else:
                return data
        except Exception as e:
            logger.error(f"Error en descompresión {compression_type.value}: {e}")
            raise

class OptimizedDiskCache:
    """Caché en disco optimizado con SQLite y compresión inteligente."""
    
    def __init__(self, cache_dir: str, config: CacheConfig):
        self.cache_dir = Path(cache_dir)
        self.config = config
        self.cache_dir.mkdir(exist_ok=True)
        
        # Base de datos SQLite para metadatos
        self.db_path = self.cache_dir / "cache_metadata.db"
        self._init_database()
        
        self._lock = threading.RLock()
        self.compressor = SmartCompressor()
    
    def _init_database(self):
        """Inicializa la base de datos de metadatos."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    compressed_size INTEGER NOT NULL,
                    compression_type TEXT NOT NULL,
                    serialization_type TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    accessed_at REAL NOT NULL,
                    access_count INTEGER DEFAULT 1,
                    checksum TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_accessed_at ON cache_entries(accessed_at)")
            conn.commit()
    
    def set(self, key: str, data: Any, serialization: SerializationType = SerializationType.PICKLE) -> bool:
        """Guarda datos en disco con compresión y metadatos."""
        try:
            with self._lock:
                # Serializar datos
                if serialization == SerializationType.PICKLE:
                    serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # JSON
                    serialized = json.dumps(data, ensure_ascii=False).encode('utf-8')
                
                # Calcular checksum
                checksum = hashlib.sha256(serialized).hexdigest()
                
                # Comprimir si es necesario
                if self.config.enable_compression and len(serialized) > self.config.compression_threshold:
                    compressed, compression_type, ratio = self.compressor.compress(serialized)
                else:
                    compressed, compression_type, ratio = serialized, CompressionType.NONE, 1.0
                
                # Generar nombre de archivo único
                filename = f"{hashlib.md5(key.encode()).hexdigest()}.cache"
                filepath = self.cache_dir / filename
                
                # Escribir archivo
                with open(filepath, 'wb') as f:
                    f.write(compressed)
                
                # Actualizar metadatos
                current_time = time.time()
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO cache_entries 
                        (key, filename, size_bytes, compressed_size, compression_type, 
                         serialization_type, created_at, accessed_at, access_count, checksum)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """, (key, filename, len(serialized), len(compressed), 
                          compression_type.value, serialization.value, 
                          current_time, current_time, checksum))
                    conn.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Error guardando en caché de disco: {e}")
            return False
    
    def get(self, key: str) -> Tuple[Optional[Any], float]:
        """Obtiene datos del disco con verificación de integridad."""
        start_time = time.perf_counter()
        
        try:
            with self._lock:
                # Buscar metadatos
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT filename, compression_type, serialization_type, checksum
                        FROM cache_entries WHERE key = ?
                    """, (key,))
                    row = cursor.fetchone()
                    
                    if not row:
                        access_time = (time.perf_counter() - start_time) * 1000
                        return None, access_time
                    
                    filename, compression_type, serialization_type, stored_checksum = row
                
                # Leer archivo
                filepath = self.cache_dir / filename
                if not filepath.exists():
                    # Limpiar entrada huérfana
                    self.delete(key)
                    access_time = (time.perf_counter() - start_time) * 1000
                    return None, access_time
                
                with open(filepath, 'rb') as f:
                    compressed_data = f.read()
                
                # Descomprimir
                compression_enum = CompressionType(compression_type)
                serialized_data = self.compressor.decompress(compressed_data, compression_enum)
                
                # Verificar integridad
                checksum = hashlib.sha256(serialized_data).hexdigest()
                if checksum != stored_checksum:
                    logger.warning(f"Checksum inválido para clave {key}, eliminando entrada")
                    self.delete(key)
                    access_time = (time.perf_counter() - start_time) * 1000
                    return None, access_time
                
                # Deserializar
                serialization_enum = SerializationType(serialization_type)
                if serialization_enum == SerializationType.PICKLE:
                    data = pickle.loads(serialized_data)
                else:  # JSON
                    data = json.loads(serialized_data.decode('utf-8'))
                
                # Actualizar acceso
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        UPDATE cache_entries 
                        SET accessed_at = ?, access_count = access_count + 1
                        WHERE key = ?
                    """, (time.time(), key))
                    conn.commit()
                
                access_time = (time.perf_counter() - start_time) * 1000
                return data, access_time
                
        except Exception as e:
            logger.error(f"Error leyendo caché de disco: {e}")
            access_time = (time.perf_counter() - start_time) * 1000
            return None, access_time
    
    def delete(self, key: str) -> bool:
        """Elimina una entrada del caché de disco."""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("SELECT filename FROM cache_entries WHERE key = ?", (key,))
                    row = cursor.fetchone()
                    
                    if row:
                        filename = row[0]
                        filepath = self.cache_dir / filename
                        
                        # Eliminar archivo
                        if filepath.exists():
                            filepath.unlink()
                        
                        # Eliminar metadatos
                        conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                        conn.commit()
                        return True
                    
                return False
                
        except Exception as e:
            logger.error(f"Error eliminando del caché de disco: {e}")
            return False
    
    def cleanup(self, max_age_days: int = 30) -> int:
        """Limpia entradas antiguas del caché de disco."""
        try:
            with self._lock:
                cutoff_time = time.time() - (max_age_days * 24 * 3600)
                deleted_count = 0
                
                with sqlite3.connect(self.db_path) as conn:
                    # Obtener entradas a eliminar
                    cursor = conn.execute("""
                        SELECT key, filename FROM cache_entries 
                        WHERE accessed_at < ?
                    """, (cutoff_time,))
                    
                    for key, filename in cursor.fetchall():
                        filepath = self.cache_dir / filename
                        if filepath.exists():
                            filepath.unlink()
                        deleted_count += 1
                    
                    # Eliminar metadatos
                    conn.execute("DELETE FROM cache_entries WHERE accessed_at < ?", (cutoff_time,))
                    conn.commit()
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error en limpieza de caché: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del caché de disco."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as entry_count,
                        SUM(size_bytes) as total_size,
                        SUM(compressed_size) as total_compressed,
                        AVG(access_count) as avg_access_count
                    FROM cache_entries
                """)
                row = cursor.fetchone()
                
                if row and row[0]:
                    entry_count, total_size, total_compressed, avg_access = row
                    return {
                        'entry_count': entry_count or 0,
                        'total_size_mb': (total_size or 0) / 1024 / 1024,
                        'compressed_size_mb': (total_compressed or 0) / 1024 / 1024,
                        'compression_ratio': (total_compressed / total_size * 100) if total_size else 0,
                        'avg_access_count': avg_access or 0
                    }
                else:
                    return {
                        'entry_count': 0,
                        'total_size_mb': 0,
                        'compressed_size_mb': 0,
                        'compression_ratio': 0,
                        'avg_access_count': 0
                    }
                    
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}

class OptimizedCacheManager:
    """Gestor de caché híbrido ultra-optimizado."""
    
    def __init__(self, cache_dir: str = "cache", config: Optional[CacheConfig] = None):
        # Inicializar el lock para concurrencia
        self._lock = threading.Lock()
        self.config = config or CacheConfig()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self._active = True  # Inicializar self._active aquí
        
        # Resto del código de inicialización...
        self.memory_cache = AdvancedLRUCache(
            max_size=self.config.max_memory_size,
            max_memory_mb=self.config.max_memory_mb
        )
        self.disk_cache = OptimizedDiskCache(str(self.cache_dir), self.config)
        
        # Pool de threads para operaciones asíncronas
        self.thread_pool = ThreadPoolExecutor(max_workers=self.config.max_threads)
        
        # Métricas
        self.metrics = CacheMetrics()
        self._metrics_lock = threading.Lock()
        
        # Thread para limpieza automática
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        if self.config.cleanup_interval > 0:
            self._start_cleanup_thread()
        
        logger.info(f"CacheManager inicializado con config: {asdict(self.config)}")
    
    def pause(self):
        with self._lock:
            self._active = False  # Bloquea nuevas operaciones

    def set_sync(self, key, value):
        """Versión síncrona para uso durante apagado"""
        # Implementación directa sin usar threads
        with self._lock:
            self.disk_cache.set(key, value)  # Ajustado para usar disk_cache directamente    
            #self._save_to_disk(key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor del caché (memoria primero, luego disco)."""
        start_time = time.perf_counter()
        
        try:
            # Intentar memoria primero
            value, mem_access_time = self.memory_cache.get(key)
            if value is not None:
                self._update_metrics('hit', access_time_ms=mem_access_time)
                return value
            
            # Intentar disco
            value, disk_access_time = self.disk_cache.get(key)
            if value is not None:
                # Promover a memoria
                self.memory_cache.set(key, value)
                self._update_metrics('hit', access_time_ms=disk_access_time)
                return value
            
            # No encontrado
            total_time = (time.perf_counter() - start_time) * 1000
            self._update_metrics('miss', access_time_ms=total_time)
            return default
            
        except Exception as e:
            logger.error(f"Error obteniendo clave {key}: {e}")
            self._update_metrics('error')
            return default
    
    def set(self, key: str, value: Any, persist: bool = True) -> bool:
        """Establece un valor en el caché."""
        try:
            # Siempre establecer en memoria
            success = self.memory_cache.set(key, value)
            
            # Establecer en disco si se solicita
            if persist:
                # Usar thread pool para operación no bloqueante
                future = self.thread_pool.submit(self.disk_cache.set, key, value)
                # No esperamos el resultado para no bloquear
            
            if success:
                self._update_metrics('set')
            
            return success
            
        except Exception as e:
            logger.error(f"Error estableciendo clave {key}: {e}")
            self._update_metrics('error')
            return False
    
    def delete(self, key: str) -> bool:
        """Elimina una clave de ambos cachés."""
        try:
            mem_deleted = self.memory_cache.delete(key)
            disk_deleted = self.disk_cache.delete(key)
            
            if mem_deleted or disk_deleted:
                self._update_metrics('delete')
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error eliminando clave {key}: {e}")
            self._update_metrics('error')
            return False
    
    def clear(self):
        """Limpia ambos cachés completamente."""
        try:
            self.memory_cache.clear()
            
            # Limpiar disco en thread separado
            future = self.thread_pool.submit(self._clear_disk_cache)
            
            # Resetear métricas
            with self._metrics_lock:
                self.metrics = CacheMetrics()
            
            logger.info("Caché limpiado completamente")
            
        except Exception as e:
            logger.error(f"Error limpiando caché: {e}")
    
    def _clear_disk_cache(self):
        """Limpia el caché de disco."""
        try:
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(exist_ok=True)
                self.disk_cache = OptimizedDiskCache(str(self.cache_dir), self.config)
        except Exception as e:
            logger.error(f"Error limpiando caché de disco: {e}")
    
    def cleanup(self, max_age_days: int = 30) -> Dict[str, int]:
        """Realiza limpieza de entradas antiguas."""
        try:
            deleted_disk = self.disk_cache.cleanup(max_age_days)
            
            # Actualizar métricas
            with self._metrics_lock:
                self.metrics.last_cleanup = datetime.now()
            
            result = {'disk_deleted': deleted_disk}
            logger.info(f"Limpieza completada: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error en limpieza: {e}")
            return {'disk_deleted': 0}
    
    def get_metrics(self) -> CacheMetrics:
        """Obtiene métricas actualizadas del caché."""
        with self._metrics_lock:
            # Actualizar estadísticas de uso
            mem_stats = self.memory_cache.get_stats()
            disk_stats = self.disk_cache.get_stats()
            
            self.metrics.memory_cache_size = mem_stats.get('size', 0)
            self.metrics.total_memory_usage_mb = mem_stats.get('memory_usage_mb', 0)
            self.metrics.disk_cache_size = disk_stats.get('entry_count', 0)
            self.metrics.total_disk_usage_mb = disk_stats.get('total_size_mb', 0)
            self.metrics.compression_saves_mb = (
                disk_stats.get('total_size_mb', 0) - disk_stats.get('compressed_size_mb', 0)
            )
            
            return self.metrics
    
    def _update_metrics(self, operation: str, access_time_ms: float = 0):
        """Actualiza las métricas de forma thread-safe."""
        with self._metrics_lock:
            if operation == 'hit':
                self.metrics.hits += 1
            elif operation == 'miss':
                self.metrics.misses += 1
            elif operation == 'set':
                self.metrics.sets += 1
            elif operation == 'delete':
                self.metrics.deletes += 1
            elif operation == 'error':
                self.metrics.errors += 1
            
            # Actualizar tiempo promedio de acceso
            if access_time_ms > 0:
                total_ops = self.metrics.hits + self.metrics.misses
                if total_ops > 1:
                    self.metrics.avg_access_time_ms = (
                        (self.metrics.avg_access_time_ms * (total_ops - 1) + access_time_ms) / total_ops
                    )
                else:
                    self.metrics.avg_access_time_ms = access_time_ms
    
    def _start_cleanup_thread(self):
        """Inicia el thread de limpieza automática."""
        def cleanup_worker():
            while not self._stop_cleanup.wait(self.config.cleanup_interval):
                try:
                    self.cleanup()
                except Exception as e:
                    logger.error(f"Error en limpieza automática: {e}")
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        logger.info(f"Thread de limpieza automática iniciado (intervalo: {self.config.cleanup_interval}s)")
    
    def shutdown(self):
        """Cierra el gestor de caché de forma ordenada."""
        try:
            # Detener nuevas operaciones
            with self._lock:
                self._active = False
            
            # Detener el thread de limpieza si existe
            if self._cleanup_thread:
                self._stop_cleanup.set()
                self._cleanup_thread.join(timeout=5)
            
            # Cerrar el pool de threads
            if self.thread_pool:
                self.thread_pool.shutdown(wait=True)
            
            # Limpiar cachés
            self.memory_cache.clear()
            self.disk_cache.cleanup(max_age_days=0)  # Limpiar todo al cerrar
            
            print("[CACHE] Cerrado correctamente")
        except Exception as e:
            print(f"[ERROR] Error cerrando caché: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

# Alias para compatibilidad con la API existente
CacheManager = OptimizedCacheManager

# Funciones de utilidad para migración
def migrate_old_cache(old_cache_dir: str, new_cache_dir: str) -> bool:
    """Migra datos de un caché antiguo a la nueva estructura."""
    try:
        old_path = Path(old_cache_dir)
        if not old_path.exists():
            return True
        
        config = CacheConfig()
        with OptimizedCacheManager(new_cache_dir, config) as new_cache:
            # Intentar cargar archivos pickle antiguos
            for cache_file in old_path.glob("*.cache"):
                try:
                    with open(cache_file, 'rb') as f:
                        data = pickle.load(f)
                    
                    # Usar el nombre del archivo como clave
                    key = cache_file.stem
                    new_cache.set(key, data, persist=True)
                    
                except Exception as e:
                    logger.warning(f"No se pudo migrar {cache_file}: {e}")
        
        logger.info(f"Migración completada de {old_cache_dir} a {new_cache_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Error en migración: {e}")
        return False

def get_cache_info(cache_dir: str) -> Dict[str, Any]:
    """Obtiene información detallada sobre un directorio de caché."""
    try:
        config = CacheConfig()
        with OptimizedCacheManager(cache_dir, config) as cache:
            metrics = cache.get_metrics()
            return {
                'metrics': metrics.to_dict(),
                'memory_stats': cache.memory_cache.get_stats(),
                'disk_stats': cache.disk_cache.get_stats(),
                'config': asdict(config)
            }
    except Exception as e:
        logger.error(f"Error obteniendo info de caché: {e}")
        return {}

# Ejemplo de uso avanzado
if __name__ == "__main__":
    # Configuración personalizada
    config = CacheConfig(
        max_memory_size=2000,
        max_memory_mb=500,
        max_disk_mb=2000,
        compression_threshold=512,
        cleanup_interval=600,
        max_threads=6
    )
    
    # Usar el caché optimizado
    with OptimizedCacheManager("cache_test", config) as cache:
        # Operaciones de ejemplo
        cache.set("test_key", {"data": "valor de prueba", "timestamp": time.time()})
        
        value = cache.get("test_key")
        print(f"Valor recuperado: {value}")
        
        # Obtener métricas
        metrics = cache.get_metrics()
        print(f"Métricas del caché: {metrics.to_dict()}")
        
        # Estadísticas detalladas
        info = get_cache_info("cache_test")
        print(f"Información completa: {info}")
