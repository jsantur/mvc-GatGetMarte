# constants.py - Constantes centralizadas del sistema

# Importar utilidades centralizadas
from utils import UI_CONSTANTS, should_show_unit, ToastNotification

# Re-exportar para compatibilidad con código existente
__all__ = ['UI_CONSTANTS', 'should_show_unit', 'ToastNotification']