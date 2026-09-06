#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para verificar el estado del archivo Excel
"""

import os
import pandas as pd
from datetime import datetime
import openpyxl

def diagnosticar_excel():
    """Diagnostica el estado del archivo Excel."""
    
    archivo_excel = "unidades_registro.xlsx"
    
    print("=" * 60)
    print("🔍 DIAGNÓSTICO DEL ARCHIVO EXCEL")
    print("=" * 60)
    
    # 1. Verificar existencia del archivo
    print(f"📁 Verificando archivo: {archivo_excel}")
    if os.path.exists(archivo_excel):
        print(f"✅ Archivo existe")
        
        # Información del archivo
        stat = os.stat(archivo_excel)
        print(f"📊 Tamaño: {stat.st_size} bytes")
        print(f"🕰️ Última modificación: {datetime.fromtimestamp(stat.st_mtime)}")
        print(f"📅 Creado: {datetime.fromtimestamp(stat.st_ctime)}")
    else:
        print(f"❌ Archivo NO existe")
        return False
    
    # 2. Intentar leer con pandas
    print(f"\n📖 Leyendo archivo con pandas...")
    try:
        df = pd.read_excel(archivo_excel, engine='openpyxl')
        print(f"✅ Archivo leído correctamente con pandas")
        print(f"📊 Filas: {len(df)}")
        print(f"📋 Columnas: {len(df.columns)}")
        print(f"📝 Nombres de columnas: {list(df.columns)}")
        
        if not df.empty:
            print(f"\n📈 Últimas 3 filas:")
            print(df.tail(3).to_string(index=False))
        else:
            print(f"⚠️ El DataFrame está vacío")
            
    except Exception as e:
        print(f"❌ Error leyendo con pandas: {e}")
        return False
    
    # 3. Intentar leer con openpyxl
    print(f"\n📖 Leyendo archivo con openpyxl...")
    try:
        workbook = openpyxl.load_workbook(archivo_excel)
        worksheet = workbook.active
        
        if worksheet is None:
            print(f"❌ No se pudo obtener el worksheet activo")
            return False
            
        print(f"✅ Archivo leído correctamente con openpyxl")
        print(f"📊 Filas en worksheet: {worksheet.max_row}")
        print(f"📋 Columnas en worksheet: {worksheet.max_column}")
        
        # Mostrar encabezados
        headers = []
        for col in range(1, worksheet.max_column + 1):
            cell_value = worksheet.cell(row=1, column=col).value
            headers.append(cell_value)
        print(f"📝 Encabezados: {headers}")
        
        # Mostrar últimas filas
        if worksheet.max_row > 1:
            print(f"\n📈 Últimas 3 filas (openpyxl):")
            for row in range(max(2, worksheet.max_row - 2), worksheet.max_row + 1):
                row_data = []
                for col in range(1, worksheet.max_column + 1):
                    cell_value = worksheet.cell(row=row, column=col).value
                    row_data.append(str(cell_value) if cell_value is not None else "")
                print(f"Fila {row}: {row_data}")
        
    except Exception as e:
        print(f"❌ Error leyendo con openpyxl: {e}")
        return False
    
    # 4. Verificar permisos
    print(f"\n🔐 Verificando permisos...")
    try:
        # Intentar abrir en modo escritura
        with open(archivo_excel, 'r+b') as f:
            print(f"✅ Permisos de lectura/escritura OK")
    except Exception as e:
        print(f"❌ Error de permisos: {e}")
    
    # 5. Verificar si está siendo usado por otra aplicación
    print(f"\n🔍 Verificando si el archivo está en uso...")
    try:
        # Intentar abrir el archivo para ver si está bloqueado
        workbook = openpyxl.load_workbook(archivo_excel, data_only=True)
        workbook.close()
        print(f"✅ Archivo no está siendo usado por otra aplicación")
    except Exception as e:
        print(f"⚠️ Posible conflicto: {e}")
    
    print(f"\n" + "=" * 60)
    print(f"✅ DIAGNÓSTICO COMPLETADO")
    print(f"=" * 60)
    
    return True

if __name__ == "__main__":
    diagnosticar_excel() 