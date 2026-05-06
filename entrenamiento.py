#!/usr/bin/env python3
"""Script de entrenamiento diario del modelo ML"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from utils.logger import log_info, log_error
from core.ml_model import MLModel
from utils.data_manager import DataManager


def main():
    """Ejecuta el entrenamiento del modelo ML."""
    try:
        # Validar configuración
        if not Settings.inicializar():
            log_error("❌ Configuración inválida.")
            sys.exit(1)
        
        Settings.crear_directorios()
        DataManager.inicializar_db()
        
        log_info("=" * 50)
        log_info("🤖 EDGE BOT - ENTRENAMIENTO ML DIARIO")
        log_info("=" * 50)
        
        # Inicializar modelo
        ml_model = MLModel()
        
        # Cargar modelo existente o crear nuevo
        if ml_model.cargar_modelo():
            log_info("✅ Modelo existente cargado")
        else:
            log_info("⚠️ No hay modelo existente, se creará uno nuevo")
        
        # Ejecutar entrenamiento
        log_info("Iniciando proceso de entrenamiento...")
        
        if ml_model.entrenar_modelo():
            log_info("✅ Entrenamiento completado exitosamente")
            
            # Mostrar importancia de características
            importancia = ml_model.obtener_importancia_caracteristicas()
            if importancia:
                log_info("\n📊 TOP 5 CARACTERÍSTICAS MÁS IMPORTANTES:")
                sorted_imp = sorted(importancia.items(), key=lambda x: x[1], reverse=True)[:5]
                for i, (feature, score) in enumerate(sorted_imp, 1):
                    log_info(f"   {i}. {feature}: {score:.2%}")
            
            sys.exit(0)
        else:
            log_error("❌ Entrenamiento fallido")
            sys.exit(1)
        
    except KeyboardInterrupt:
        log_info("\n⚠️ Entrenamiento detenido por usuario")
        sys.exit(0)
    except Exception as e:
        log_error(f"Error crítico en entrenamiento: {e}")
        import traceback
        log_error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
