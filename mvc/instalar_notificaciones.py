#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de instalación para el sistema de notificaciones
"""

import subprocess
import sys
import os
import json
from pathlib import Path

def instalar_dependencias():
    """Instala las dependencias necesarias."""
    print("📦 Instalando dependencias...")
    
    dependencias = [
        "plyer>=2.0.0",
        "pytz"
    ]
    
    for dep in dependencias:
        try:
            print(f"  Instalando {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"  ✅ {dep} instalado correctamente")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Error al instalar {dep}: {e}")
            return False
    
    return True

def crear_configuracion_inicial():
    """Crea la configuración inicial del sistema."""
    print("⚙️ Creando configuración inicial...")
    
    config = {
        "notificacion_inicial_mostrada": False,
        "ultimo_recordatorio": None,
        "sms_enabled": False,
        "sms_api_key": ""
    }
    
    try:
        with open("notificacion_config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("  ✅ Configuración creada correctamente")
        return True
    except Exception as e:
        print(f"  ❌ Error al crear configuración: {e}")
        return False

def verificar_archivos():
    """Verifica que los archivos necesarios estén presentes."""
    print("🔍 Verificando archivos...")
    
    archivos_requeridos = [
        "notificacion.py",
        "test_notificacion.py"
    ]
    
    archivos_faltantes = []
    for archivo in archivos_requeridos:
        if not os.path.exists(archivo):
            archivos_faltantes.append(archivo)
        else:
            print(f"  ✅ {archivo} encontrado")
    
    if archivos_faltantes:
        print(f"  ❌ Archivos faltantes: {archivos_faltantes}")
        return False
    
    return True

def probar_sistema():
    """Ejecuta una prueba rápida del sistema."""
    print("🧪 Probando sistema...")
    
    try:
        # Importar y probar el sistema
        from notificacion import iniciar_sistema_notificaciones, detener_sistema_notificaciones
        
        print("  Iniciando sistema de prueba...")
        sistema = iniciar_sistema_notificaciones()
        
        print("  Deteniendo sistema...")
        detener_sistema_notificaciones()
        
        print("  ✅ Sistema funcionando correctamente")
        return True
        
    except Exception as e:
        print(f"  ❌ Error en prueba del sistema: {e}")
        return False

def mostrar_instrucciones():
    """Muestra las instrucciones de uso."""
    print("\n" + "="*60)
    print("🎉 INSTALACIÓN COMPLETADA")
    print("="*60)
    print("\n📋 Cómo usar el sistema:")
    print("1. Ejecutar independientemente:")
    print("   python notificacion.py")
    print("\n2. Ejecutar prueba:")
    print("   python test_notificacion.py")
    print("\n3. Integrar en tu código:")
    print("   from notificacion import iniciar_sistema_notificaciones")
    print("   sistema = iniciar_sistema_notificaciones()")
    print("\n📖 Para más información, consulta README_notificaciones.md")
    print("\n🔔 El sistema mostrará notificaciones automáticamente")
    print("   en los horarios configurados para cada turno.")

def main():
    """Función principal de instalación."""
    print("🔔 INSTALADOR DEL SISTEMA DE NOTIFICACIONES")
    print("="*50)
    
    # Verificar Python
    if sys.version_info < (3, 6):
        print("❌ Se requiere Python 3.6 o superior")
        return 1
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detectado")
    
    # Verificar archivos
    if not verificar_archivos():
        print("❌ Faltan archivos necesarios")
        return 1
    
    # Instalar dependencias
    if not instalar_dependencias():
        print("❌ Error al instalar dependencias")
        return 1
    
    # Crear configuración
    if not crear_configuracion_inicial():
        print("❌ Error al crear configuración")
        return 1
    
    # Probar sistema
    if not probar_sistema():
        print("❌ Error en prueba del sistema")
        return 1
    
    # Mostrar instrucciones
    mostrar_instrucciones()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 