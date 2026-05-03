#!/usr/bin/env python3
"""Script de auditoría y aprendizaje del bot EdgeBot-IA-V2"""
import os
from core.audit import AuditManager
from config.settings import Settings
from utils.logger import log_info, log_error
from utils.data_manager import DataManager


def crear_reglas_base_si_no_existen():
    """Mantiene tus reglas base originales si el archivo es nuevo."""
    ruta = Settings.FILES["aprendizaje"]
    if not os.path.exists(ruta):
        contenido_base = """[HISTORIAL RECIENTE PARA APRENDIZAJE Y CALIBRACIÓN]
### REGLAS BASE
- [Away Elite Defense]: Reducir penalización a visitantes si son Top 5 europeo en PPDA.
- [Home Advantage Decay]: En eliminatorias con alto xG (>3.0), el factor cancha pierde 15%.
- [Extreme Altitude]: Multiplicar xGA del visitante por 1.35 en la 2da mitad en altitud.
- [Elite Roster Home Protection]: El Edge es penalizado si el pick va contra equipos de Élite en casa.
"""
        DataManager.guardar_aprendizaje(contenido_base)


def main():
    """Ejecuta el sistema de auditoría y aprendizaje."""
    try:
        Settings.crear_directorios()
        crear_reglas_base_si_no_existen()
        
        audit_manager = AuditManager()
        audit_manager.ejecutar()
    except Exception as e:
        log_error(f"Error crítico en auditoría: {e}")
        raise


if __name__ == "__main__":
    main()
