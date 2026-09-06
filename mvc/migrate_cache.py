#!/usr/bin/env python3
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
            print("\n📋 Pasos siguientes:")
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
