#!/usr/bin/env python3
"""Script principal del bot EdgeBot-IA-V2"""
from core.analyzer import EdgeBotAnalyzer
from config.settings import Settings
from utils.logger import log_info, log_error


def main():
    """Ejecuta el bot principal."""
    try:
        Settings.crear_directorios()
        analyzer = EdgeBotAnalyzer()
        analyzer.ejecutar()
    except Exception as e:
        log_error(f"Error crítico: {e}")
        raise


if __name__ == "__main__":
    main()
