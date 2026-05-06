#!/usr/bin/env python3
"""Script principal del bot EdgeBot-IA-V2 con ML"""
from core.analyzer import EdgeBotAnalyzer
from config.settings import Settings
from utils.logger import log_info, log_error
from utils.data_manager import DataManager
import sys


def main():
    """Ejecuta el bot principal con validación de configuración."""
    try:
        if not Settings.inicializar():
            log_error("❌ Configuración inválida. El bot no puede iniciar.")
            sys.exit(1)
        
        DataManager.inicializar_db()
        
        analyzer = EdgeBotAnalyzer()
        analyzer.ejecutar()
        
    except KeyboardInterrupt:
        log_info("\n⚠️ Bot detenido por usuario")
        sys.exit(0)
    except Exception as e:
        log_error(f"Error crítico: {e}")
        raise


if __name__ == "__main__":
    main()
