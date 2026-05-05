#!/usr/bin/env python3
"""Script de auditoría y aprendizaje del bot EdgeBot-IA-V2"""
import sys
import os

# Agregar la raíz del proyecto al path de búsqueda
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ✅ CORRECCIÓN: Import desde raíz (settings.py está en root, no en config/)
from settings import Settings
from utils.logger import log_info, log_error

# ✅ CORRECCIÓN: Verificar si existe core.audit antes de importar
try:
    from core.audit import AuditManager
    AUDIT_EXISTS = True
except ImportError:
    AuditManager = None
    AUDIT_EXISTS = False

# ✅ CORRECCIÓN: Verificar si existe data_manager
try:
    from utils.data_manager import DataManager
    DM_EXISTS = True
except ImportError:
    DataManager = None
    DM_EXISTS = False


def crear_reglas_base_si_no_existen():
    """Mantiene las reglas base originales si el archivo es nuevo."""
    ruta = Settings.FILES["aprendizaje"]
    if not os.path.exists(ruta):
        contenido_base = """[HISTORIAL RECIENTE PARA APRENDIZAJE Y CALIBRACIÓN]
### REGLAS BASE
- [Away Elite Defense]: Reducir penalización a visitantes si son Top 5 europeo en PPDA.
- [Home Advantage Decay]: En eliminatorias con alto xG (>3.0), el factor cancha pierde 15%.
- [Extreme Altitude]: Multiplicar xGA del visitante por 1.35 en la 2da mitad en altitud.
- [Elite Roster Home Protection]: El Edge es penalizado si el pick va contra equipos de Élite en casa.
"""
        # ✅ CORRECCIÓN: Usar DataManager solo si existe
        if DM_EXISTS:
            DataManager.guardar_aprendizaje(contenido_base)
        else:
            # Fallback: guardar directamente
            os.makedirs(Settings.DATA_DIR, exist_ok=True)
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido_base)
        log_info("✅ Reglas base creadas")


def main():
    """Ejecuta el sistema de auditoría y aprendizaje."""
    try:
        # Validar configuración
        if not Settings.inicializar():
            log_error("❌ Configuración inválida. El bot no puede iniciar.")
            sys.exit(1)
        
        Settings.crear_directorios()
        crear_reglas_base_si_no_existen()
        
        # ✅ CORRECCIÓN: Inicializar DB solo si DataManager existe
        if DM_EXISTS:
            DataManager.inicializar_db()
        
        # ✅ CORRECCIÓN: Usar AuditManager solo si existe
        if AUDIT_EXISTS and AuditManager:
            audit_manager = AuditManager()
            audit_manager.ejecutar()
        else:
            log_error("❌ Módulo de auditoría no disponible (core.audit.py faltante)")
            sys.exit(1)
        
    except KeyboardInterrupt:
        log_info("\n⚠️ Auditoría detenida por usuario")
        sys.exit(0)
    except Exception as e:
        log_error(f"Error crítico en auditoría: {e}")
        raise


if __name__ == "__main__":
    main()
