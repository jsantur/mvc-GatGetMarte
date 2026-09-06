# units_manager.py - Gestión centralizada de unidades
"""
Módulo centralizado para la gestión de unidades del sistema.
Unifica toda la lógica relacionada con unidades para evitar duplicación.
"""

import os
import threading
from typing import Dict, List, Tuple, Optional, Set, Any
from pathlib import Path
import json
import pickle
from datetime import datetime
from utils import safe_file_operation, get_base_path

class UnitsManager:
    """Gestor centralizado de unidades con validación robusta y caché."""
    
    def __init__(self, units_file: str = "unidades.txt"):
        self.units_file = units_file
        self._lock = threading.Lock()
        
        # Datos de unidades
        self.alias_unidades: Dict[str, str] = {}
        self.camionetas: Set[str] = set()
        self.autos: Set[str] = set()
        self.unidades_disponibles: List[str] = []
        
        # Plantilla por defecto
        self.default_template = [
            "🚙 1 EUI-621;EUI-621;PICKUP",
            "🚙 2 EUI-682;EUI-682;PICKUP",
            "🚙 3 EUI-683;EUI-683;PICKUP",
            "🚙 4 EUI-646;EUI-646;PICKUP",
            "🚙 5 EUI-685;EUI-685;PICKUP",
            "🚙 6 EUI-686;EUI-686;PICKUP",
            "🚙 7 EUI-679;EUI-679;PICKUP",
            "🚙 8 EUI-680;EUI-680;PICKUP",
            "🚘 9 EUI-645;EUI-645;AUTO",
            "🚘 10 EUI-647;EUI-647;AUTO",
            "🚘 11 EUI-668;EUI-668;AUTO",
            "🚘 12 EUI-670;EUI-670;AUTO",
            "🚘 13 EUI-671;EUI-671;AUTO"
        ]
        
        # Cargar unidades al inicializar
        self.load_units()
    
    @safe_file_operation
    def load_units(self) -> bool:
        """Carga las unidades desde el archivo con validación robusta."""
        with self._lock:
            try:
                # Asegurar que el archivo existe y es válido
                if not self.ensure_file_exists():
                    print("[ERROR] No se pudo crear o validar el archivo unidades.txt")
                    return False
                
                # Limpiar datos existentes
                self.alias_unidades.clear()
                self.camionetas.clear()
                self.autos.clear()
                self.unidades_disponibles.clear()
                
                # Leer archivo
                with open(self.units_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line or not self._validate_line_format(line):
                            print(f"[ADVERTENCIA] Línea {line_num} ignorada: formato inválido")
                            continue
                        
                        try:
                            alias, codigo, tipo = line.split(';')
                            self.alias_unidades[alias] = codigo
                            self.unidades_disponibles.append(alias)
                            
                            if tipo == 'PICKUP':
                                self.camionetas.add(codigo)
                            elif tipo == 'AUTO':
                                self.autos.add(codigo)
                            else:
                                print(f"[ADVERTENCIA] Tipo desconocido '{tipo}' para unidad {alias}")
                                
                        except Exception as e:
                            print(f"[ERROR] Error procesando línea {line_num}: {e}")
                            continue
                
                print(f"[ÉXITO] Cargadas {len(self.unidades_disponibles)} unidades: "
                      f"{len(self.camionetas)} pickup, {len(self.autos)} autos")
                return True
                
            except Exception as e:
                print(f"[ERROR] Error cargando unidades: {e}")
                return self._load_default_configuration()
    
    def ensure_file_exists(self) -> bool:
        """Asegura que el archivo de unidades existe y es válido."""
        try:
            if not os.path.exists(self.units_file):
                return self._create_from_template()
            
            # Verificar que el archivo no esté vacío
            if os.path.getsize(self.units_file) == 0:
                print("[ADVERTENCIA] Archivo unidades.txt está vacío")
                return self._create_from_template()
            
            # Verificar que al menos una línea sea válida
            with open(self.units_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip() and self._validate_line_format(line.strip()):
                        return True
            
            print("[ADVERTENCIA] No se encontraron líneas válidas en unidades.txt")
            return self._create_from_template()
            
        except Exception as e:
            print(f"[ERROR] Error verificando archivo: {e}")
            return self._create_from_template()
    
    def _create_from_template(self) -> bool:
        """Crea el archivo desde la plantilla por defecto."""
        try:
            with open(self.units_file, 'w', encoding='utf-8') as f:
                for line in self.default_template:
                    f.write(line + '\n')
            print(f"[ÉXITO] Archivo {self.units_file} creado desde plantilla")
            return True
        except Exception as e:
            print(f"[ERROR] Error creando archivo desde plantilla: {e}")
            return False
    
    def _validate_line_format(self, line: str) -> bool:
        """Valida que una línea tenga el formato correcto: 'alias;codigo;tipo'."""
        try:
            if ';' not in line:
                return False
            
            parts = line.split(';')
            if len(parts) != 3:
                return False
            
            alias, codigo, tipo = parts
            
            # Validar que los campos no estén vacíos
            if not alias.strip() or not codigo.strip() or not tipo.strip():
                return False
            
            # Validar que el tipo sea válido
            if tipo.strip().upper() not in ['PICKUP', 'AUTO']:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _load_default_configuration(self) -> bool:
        """Carga configuración por defecto en caso de error."""
        print("[ADVERTENCIA] Usando configuración por defecto")
        
        self.alias_unidades.clear()
        self.camionetas.clear()
        self.autos.clear()
        self.unidades_disponibles.clear()
        
        for line in self.default_template:
            try:
                alias, codigo, tipo = line.split(';')
                self.alias_unidades[alias] = codigo
                self.unidades_disponibles.append(alias)
                
                if tipo == 'PICKUP':
                    self.camionetas.add(codigo)
                elif tipo == 'AUTO':
                    self.autos.add(codigo)
            except Exception:
                continue
        
        return True
    
    def add_unit(self, alias: str, codigo: str, tipo: str) -> bool:
        """Agrega una nueva unidad al archivo."""
        try:
            with self._lock:
                # Validar datos
                if not alias or not codigo or tipo.upper() not in ['PICKUP', 'AUTO']:
                    print("[ERROR] Datos inválidos para nueva unidad")
                    return False
                
                # Verificar que la unidad no exista
                if alias in self.alias_unidades:
                    print(f"[ERROR] La unidad {alias} ya existe")
                    return False
                
                # Agregar al archivo
                with open(self.units_file, 'a', encoding='utf-8') as f:
                    f.write(f"{alias};{codigo};{tipo.upper()}\n")
                
                # Actualizar datos en memoria
                self.alias_unidades[alias] = codigo
                self.unidades_disponibles.append(alias)
                
                if tipo.upper() == 'PICKUP':
                    self.camionetas.add(codigo)
                else:
                    self.autos.add(codigo)
                
                print(f"[ÉXITO] Unidad {alias} agregada exitosamente")
                return True
                
        except Exception as e:
            print(f"[ERROR] Error agregando unidad: {e}")
            return False
    
    def remove_unit(self, alias: str) -> bool:
        """Elimina una unidad del archivo."""
        try:
            with self._lock:
                if alias not in self.alias_unidades:
                    print(f"[ERROR] La unidad {alias} no existe")
                    return False
                
                # Leer todas las líneas excepto la de la unidad a eliminar
                lines = []
                with open(self.units_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip().startswith(f"{alias};"):
                            lines.append(line)
                
                # Reescribir archivo
                with open(self.units_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                # Actualizar datos en memoria
                codigo = self.alias_unidades.pop(alias)
                self.unidades_disponibles.remove(alias)
                
                if codigo in self.camionetas:
                    self.camionetas.remove(codigo)
                elif codigo in self.autos:
                    self.autos.remove(codigo)
                
                print(f"[ÉXITO] Unidad {alias} eliminada exitosamente")
                return True
                
        except Exception as e:
            print(f"[ERROR] Error eliminando unidad: {e}")
            return False
    
    def get_units_by_type(self, unit_type: str) -> List[str]:
        """Obtiene unidades filtradas por tipo."""
        if unit_type.upper() == 'PICKUP':
            return [alias for alias in self.unidades_disponibles 
                   if self.alias_unidades.get(alias) in self.camionetas]
        elif unit_type.upper() == 'AUTO':
            return [alias for alias in self.unidades_disponibles 
                   if self.alias_unidades.get(alias) in self.autos]
        else:
            return self.unidades_disponibles.copy()
    
    def get_unit_code(self, alias: str) -> Optional[str]:
        """Obtiene el código de una unidad por su alias."""
        return self.alias_unidades.get(alias)
    
    def get_unit_type(self, alias: str) -> Optional[str]:
        """Obtiene el tipo de una unidad por su alias."""
        codigo = self.alias_unidades.get(alias)
        if codigo in self.camionetas:
            return 'PICKUP'
        elif codigo in self.autos:
            return 'AUTO'
        return None
    
    def get_all_data(self) -> Dict[str, Any]:
        """Obtiene todos los datos de unidades en un diccionario."""
        return {
            'alias_unidades': self.alias_unidades.copy(),
            'camionetas': self.camionetas.copy(),
            'autos': self.autos.copy(),
            'unidades_disponibles': self.unidades_disponibles.copy()
        }
    
    def reload_units(self) -> bool:
        """Recarga las unidades desde el archivo."""
        return self.load_units()
    
    def backup_units(self, backup_path: Optional[str] = None) -> bool:
        """Crea un respaldo de las unidades."""
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"unidades_backup_{timestamp}.txt"
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                for alias in self.unidades_disponibles:
                    codigo = self.alias_unidades[alias]
                    tipo = 'PICKUP' if codigo in self.camionetas else 'AUTO'
                    f.write(f"{alias};{codigo};{tipo}\n")
            
            print(f"[ÉXITO] Respaldo creado: {backup_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error creando respaldo: {e}")
            return False

# Instancia global del gestor de unidades
# Usar get_base_path() para compatibilidad con PyInstaller
units_manager = UnitsManager(os.path.join(get_base_path(), "unidades.txt"))