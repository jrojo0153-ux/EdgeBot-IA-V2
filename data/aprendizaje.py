#!/usr/bin/env python3
"""Script de auditoría y aprendizaje del bot EdgeBot-IA-V2"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from utils.logger import log_info, log_error

try:
    from core.audit import AuditManager
    AUDIT_EXISTS = True
except ImportError:
    AuditManager = None
    AUDIT_EXISTS = False

try:
    from utils.data_manager import DataManager
    DM_EXISTS = True
except ImportError:
    DataManager = None
    DM_EXISTS = False


def crear_reglas_base_si_no_existen():
    """Mantiene las reglas base originales."""
    ruta = Settings.FILES["aprendizaje"]
    if not os.path.exists(ruta):
        contenido_base = """[HISTORIAL RECIENTE PARA APRENDIZAJE Y CALIBRACIÓN]
### REGLAS BASE
- [Away Elite Defense]: Reducir penalización a visitantes si son Top 5 en defensa.
- [Home Advantage Decay]: En partidos con alto xG (>3.0), factor cancha pierde 15%.
- [Elite Roster Home Protection]: Edge penalizado si pick va contra equipos de Élite en casa.
"""
        if DM_EXISTS:
            DataManager.guardar_aprendizaje(contenido_base)
        else:
            os.makedirs(Settings.DATA_DIR, exist_ok=True)
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido_base)
        log_info("✅ Reglas base creadas")


def main():
    """Ejecuta el sistema de auditoría y aprendizaje."""
    try:
        if not Settings.inicializar():
            log_error("❌ Configuración inválida.")
            sys.exit(1)
        
        Settings.crear_directorios()
        crear_reglas_base_si_no_existen()
        
        if DM_EXISTS:
            DataManager.inicializar_db()
        
        if AUDIT_EXISTS and AuditManager:
            audit_manager = AuditManager()
            audit_manager.ejecutar()
        else:
            log_error("❌ Módulo de auditoría no disponible")
            sys.exit(1)
        
    except KeyboardInterrupt:
        log_info("\n⚠️ Auditoría detenida por usuario")
        sys.exit(0)
    except Exception as e:
        log_error(f"Error crítico en auditoría: {e}")
        raise


if __name__ == "__main__":
    main()
