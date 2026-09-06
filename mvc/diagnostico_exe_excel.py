#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico específico para problemas con Excel en modo .exe
"""

import os
import sys
import shutil
import pandas as pd
import openpyxl
from datetime import datetime
from pathlib import Path

def get_executable_directory():
    """Obtiene el directorio donde se ejecuta el .exe o el script."""
    if getattr(sys, 'frozen', False):
        # Si estamos en un ejecutable PyInstaller
        exe_dir = os.path.dirname(sys.executable)
        print(f"🔧 Ejecutándose como .exe desde: {exe_dir}")
        return exe_dir
    else:
        # Si estamos en desarrollo
        dev_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"🔧 Ejecutándose en desarrollo desde: {dev_dir}")
        return dev_dir

def get_base_path():
    """Obtiene la ruta base de la aplicación."""
    try:
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
            print(f"📦 Usando sys._MEIPASS: {base_path}")
        else:
            base_path = os.path.abspath(".")
            print(f"📦 Usando directorio actual: {base_path}")
    except Exception:
        base_path = os.path.abspath(".")
        print(f"📦 Fallback a directorio actual: {base_path}")
    return base_path

def check_excel_file_locations():
    """Verifica todas las posibles ubicaciones del archivo Excel."""
    print("\n" + "="*60)
    print("🔍 VERIFICANDO UBICACIONES DEL ARCHIVO EXCEL")
    print("="*60)
    
    # Lista de posibles ubicaciones
    locations = [
        ("Directorio del ejecutable", get_executable_directory()),
        ("sys._MEIPASS", get_base_path()),
        ("Directorio actual", os.getcwd()),
        ("Directorio del script", os.path.dirname(os.path.abspath(__file__))),
        ("TEMP", os.environ.get('TEMP', '')),
        ("TMP", os.environ.get('TMP', ''))
    ]
    
    excel_files_found = []
    
    for name, path in locations:
        if not path:
            continue
            
        excel_path = os.path.join(path, "unidades_registro.xlsx")
        print(f"\n📍 {name}: {path}")
        
        if os.path.exists(excel_path):
            try:
                file_size = os.path.getsize(excel_path)
                file_time = datetime.fromtimestamp(os.path.getmtime(excel_path))
                is_writable = os.access(excel_path, os.W_OK)
                
                print(f"   ✅ Archivo encontrado")
                print(f"   📏 Tamaño: {file_size} bytes")
                print(f"   🕰️ Última modificación: {file_time}")
                print(f"   🔐 Permisos escritura: {'✅ Sí' if is_writable else '❌ No'}")
                
                excel_files_found.append((name, excel_path, file_size, is_writable))
                
            except Exception as e:
                print(f"   ❌ Error accediendo al archivo: {e}")
        else:
            print(f"   ❌ Archivo no encontrado")
    
    return excel_files_found

def test_excel_operations():
    """Prueba operaciones de lectura y escritura en el archivo Excel."""
    print("\n" + "="*60)
    print("🧪 PROBANDO OPERACIONES DE EXCEL")
    print("="*60)
    
    exe_dir = get_executable_directory()
    excel_path = os.path.join(exe_dir, "unidades_registro.xlsx")
    
    if not os.path.exists(excel_path):
        print(f"❌ No se puede probar: archivo no existe en {excel_path}")
        return False
    
    # Prueba 1: Lectura con pandas
    print(f"\n📖 Prueba 1: Lectura con pandas")
    try:
        df = pd.read_excel(excel_path, engine='openpyxl')
        print(f"   ✅ Lectura exitosa con pandas")
        print(f"   📊 Filas: {len(df)}")
        print(f"   📋 Columnas: {list(df.columns)}")
    except Exception as e:
        print(f"   ❌ Error leyendo con pandas: {e}")
        return False
    
    # Prueba 2: Lectura con openpyxl
    print(f"\n📖 Prueba 2: Lectura con openpyxl")
    try:
        workbook = openpyxl.load_workbook(excel_path)
        worksheet = workbook.active
        print(f"   ✅ Lectura exitosa con openpyxl")
        print(f"   📊 Filas en worksheet: {worksheet.max_row}")
        print(f"   📋 Columnas en worksheet: {worksheet.max_column}")
        workbook.close()
    except Exception as e:
        print(f"   ❌ Error leyendo con openpyxl: {e}")
        return False
    
    # Prueba 3: Escritura (simulación de vaciar BD)
    print(f"\n✏️ Prueba 3: Simulación de vaciar BD")
    try:
        # Crear respaldo antes de la prueba
        backup_path = excel_path + ".backup_test"
        shutil.copy2(excel_path, backup_path)
        print(f"   💾 Respaldo creado: {backup_path}")
        
        # Simular operación de vaciar BD
        workbook = openpyxl.load_workbook(excel_path)
        worksheet = workbook.active
        
        # Borrar todas las filas excepto la primera
        if worksheet.max_row > 1:
            worksheet.delete_rows(2, worksheet.max_row)
            print(f"   🗑️ Filas eliminadas (dejando solo encabezados)")
        
        # Guardar cambios
        workbook.save(excel_path)
        workbook.close()
        print(f"   ✅ Archivo guardado exitosamente")
        
        # Verificar que se guardó correctamente
        df_after = pd.read_excel(excel_path, engine='openpyxl')
        print(f"   📊 Filas después de vaciar: {len(df_after)}")
        
        # Restaurar respaldo
        shutil.copy2(backup_path, excel_path)
        os.remove(backup_path)
        print(f"   🔄 Respaldo restaurado")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error en operación de escritura: {e}")
        # Intentar restaurar respaldo si existe
        if os.path.exists(backup_path):
            try:
                shutil.copy2(backup_path, excel_path)
                os.remove(backup_path)
                print(f"   🔄 Respaldo restaurado después del error")
            except:
                pass
        return False

def check_permissions_and_locks():
    """Verifica permisos y bloqueos del archivo."""
    print("\n" + "="*60)
    print("🔐 VERIFICANDO PERMISOS Y BLOQUEOS")
    print("="*60)
    
    exe_dir = get_executable_directory()
    excel_path = os.path.join(exe_dir, "unidades_registro.xlsx")
    
    if not os.path.exists(excel_path):
        print(f"❌ Archivo no existe: {excel_path}")
        return False
    
    # Verificar permisos
    print(f"\n📁 Archivo: {excel_path}")
    print(f"📏 Tamaño: {os.path.getsize(excel_path)} bytes")
    
    # Permisos de lectura
    if os.access(excel_path, os.R_OK):
        print(f"✅ Permisos de lectura: OK")
    else:
        print(f"❌ Permisos de lectura: DENEGADO")
    
    # Permisos de escritura
    if os.access(excel_path, os.W_OK):
        print(f"✅ Permisos de escritura: OK")
    else:
        print(f"❌ Permisos de escritura: DENEGADO")
    
    # Verificar si está siendo usado por otra aplicación
    print(f"\n🔍 Verificando si el archivo está en uso...")
    try:
        # Intentar abrir el archivo para ver si está bloqueado
        workbook = openpyxl.load_workbook(excel_path, data_only=True)
        workbook.close()
        print(f"✅ Archivo no está siendo usado por otra aplicación")
    except PermissionError:
        print(f"❌ Archivo está siendo usado por otra aplicación")
        return False
    except Exception as e:
        print(f"⚠️ Error verificando uso del archivo: {e}")
    
    return True

def create_test_excel():
    """Crea un archivo Excel de prueba para verificar funcionalidad."""
    print("\n" + "="*60)
    print("🔄 CREANDO ARCHIVO EXCEL DE PRUEBA")
    print("="*60)
    
    exe_dir = get_executable_directory()
    test_excel_path = os.path.join(exe_dir, "test_excel.xlsx")
    
    try:
        # Crear DataFrame de prueba
        df = pd.DataFrame({
            '🚓 UNIDADES': ['TEST-001'],
            '🚔 KM': ['100'],
            '📌 A.P': ['5'],
            '📒 P.O': ['3'],
            '🕵️‍♂️ TURNO': ['DÍA'],
            '🌙 OBS-TURNO': ['TEST'],
            '🕰️ HORA': ['12:00:00'],
            '📅 FECHA': ['01/01/2025']
        })
        
        # Guardar con formato
        with pd.ExcelWriter(test_excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Registro de Unidades')
            
            # Obtener el workbook y worksheet
            workbook = writer.book
            worksheet = writer.sheets['Registro de Unidades']
            
            # Aplicar formato a encabezados
            from openpyxl.styles import Font, Alignment, PatternFill
            
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            
            for col in range(1, 9):  # 8 columnas
                cell = worksheet.cell(row=1, column=col)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center")
        
        print(f"✅ Archivo de prueba creado: {test_excel_path}")
        
        # Verificar que se puede leer
        df_test = pd.read_excel(test_excel_path, engine='openpyxl')
        print(f"✅ Archivo de prueba leído correctamente: {len(df_test)} filas")
        
        # Limpiar archivo de prueba
        os.remove(test_excel_path)
        print(f"🗑️ Archivo de prueba eliminado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando archivo de prueba: {e}")
        return False

def main():
    """Función principal del diagnóstico."""
    print("="*60)
    print("🔍 DIAGNÓSTICO ESPECÍFICO PARA PROBLEMAS DE EXCEL EN .EXE")
    print("="*60)
    
    # Información del sistema
    print(f"\n💻 Información del sistema:")
    print(f"   Sistema operativo: {sys.platform}")
    print(f"   Python: {sys.version}")
    print(f"   Ejecutándose como .exe: {getattr(sys, 'frozen', False)}")
    
    # Verificar ubicaciones
    excel_files = check_excel_file_locations()
    
    if not excel_files:
        print(f"\n❌ No se encontró ningún archivo Excel")
        print(f"💡 Creando archivo Excel de prueba...")
        if create_test_excel():
            print(f"✅ El sistema puede crear archivos Excel")
        else:
            print(f"❌ Problema al crear archivos Excel")
        return
    
    # Verificar permisos
    if not check_permissions_and_locks():
        print(f"\n❌ Problemas con permisos o bloqueos")
        return
    
    # Probar operaciones
    if not test_excel_operations():
        print(f"\n❌ Problemas con operaciones de Excel")
        return
    
    print(f"\n" + "="*60)
    print(f"✅ DIAGNÓSTICO COMPLETADO - SIN PROBLEMAS DETECTADOS")
    print(f"="*60)
    print(f"\n💡 Si el problema persiste, verifica:")
    print(f"   1. Que no haya otras instancias de la aplicación ejecutándose")
    print(f"   2. Que el antivirus no esté bloqueando las operaciones")
    print(f"   3. Que tengas permisos de administrador en el directorio")
    print(f"   4. Que el archivo no esté abierto en Excel")

if __name__ == "__main__":
    main() 