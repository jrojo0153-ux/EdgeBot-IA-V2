"""Gestor centralizado de datos para EdgeBot-IA-V2"""
import os
import json
from datetime import datetime
from config.settings import Settings
from .logger import log_debug, log_error


class DataManager:
    """Gestiona todos los archivos de datos del bot."""
    
    @staticmethod
    def leer_aprendizaje():
        """Lee el archivo de reglas de aprendizaje."""
        try:
            ruta = Settings.FILES["aprendizaje"]
            if os.path.exists(ruta):
                with open(ruta, "r", encoding="utf-8") as f:
                    return f.read()
            return "No hay datos históricos previos."
        except Exception as e:
            log_error(f"Error al leer aprendizaje: {e}")
            return "Error al cargar aprendizaje."
    
    @staticmethod
    def guardar_aprendizaje(contenido):
        """Guarda el archivo de reglas de aprendizaje."""
        try:
            Settings.crear_directorios()
            ruta = Settings.FILES["aprendizaje"]
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido)
            log_debug(f"Aprendizaje guardado en {ruta}")
        except Exception as e:
            log_error(f"Error al guardar aprendizaje: {e}")
    
    @staticmethod
    def agregar_a_aprendizaje(nuevas_reglas):
        """Agrega nuevas reglas al archivo de aprendizaje."""
        try:
            Settings.crear_directorios()
            ruta = Settings.FILES["aprendizaje"]
            with open(ruta, "a", encoding="utf-8") as f:
                f.write(f"\n### NUEVAS REGLAS AUTOMÁTICAS\n")
                for regla in nuevas_reglas:
                    f.write(f"- {regla}\n")
            log_debug(f"Se agregaron {len(nuevas_reglas)} nuevas reglas")
        except Exception as e:
            log_error(f"Error al agregar reglas: {e}")
    
    @staticmethod
    def cargar_procesados():
        """Carga la lista de partidos ya procesados."""
        try:
            ruta = Settings.FILES["procesados"]
            if os.path.exists(ruta):
                with open(ruta, "r", encoding="utf-8") as f:
                    return f.read().splitlines()
            return []
        except Exception as e:
            log_error(f"Error al cargar procesados: {e}")
            return []
    
    @staticmethod
    def guardar_procesado(partido_id):
        """Marca un partido como procesado."""
        try:
            Settings.crear_directorios()
            ruta = Settings.FILES["procesados"]
            with open(ruta, "a", encoding="utf-8") as f:
                f.write(f"{partido_id}\n")
            log_debug(f"Procesado guardado: {partido_id}")
        except Exception as e:
            log_error(f"Error al guardar procesado: {e}")
    
    @staticmethod
    def cargar_predicciones_pendientes():
        """Carga las predicciones pendientes de auditoría."""
        try:
            ruta = Settings.FILES["predicciones_pendientes"]
            if os.path.exists(ruta):
                with open(ruta, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            log_error(f"Error al cargar predicciones pendientes: {e}")
            return {}
    
    @staticmethod
    def guardar_prediccion_pendiente(partido_id, partido_str, analisis):
        """Guarda una predicción para auditoría futura."""
        try:
            Settings.crear_directorios()
            ruta = Settings.FILES["predicciones_pendientes"]
            
            pendientes = DataManager.cargar_predicciones_pendientes()
            pendientes[partido_id] = {
                "partido_str": partido_str,
                "analisis": analisis,
                "fecha": datetime.today().strftime('%Y-%m-%d')
            }
            
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(pendientes, f, ensure_ascii=False, indent=4)
            log_debug(f"Predicción pendiente guardada: {partido_id}")
        except Exception as e:
            log_error(f"Error al guardar predicción pendiente: {e}")
    
    @staticmethod
    def actualizar_predicciones_pendientes(pendientes):
        """Actualiza el archivo de predicciones pendientes."""
        try:
            Settings.crear_directorios()
            ruta = Settings.FILES["predicciones_pendientes"]
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(pendientes, f, ensure_ascii=False, indent=4)
            log_debug(f"Predicciones pendientes actualizadas")
        except Exception as e:
            log_error(f"Error al actualizar predicciones pendientes: {e}")
    
    @staticmethod
    def agregar_historial_resultado(auditoria):
        """Agrega un resultado auditado al historial."""
        try:
            Settings.crear_directorios()
            ruta = Settings.FILES["historial"]
            with open(ruta, "a", encoding="utf-8") as f:
                f.write(f"\n{auditoria}")
            log_debug(f"Historial actualizado")
        except Exception as e:
            log_error(f"Error al agregar al historial: {e}")
