"""Gestor centralizado de datos para EdgeBot-IA-V2 con SQLite"""
import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import contextmanager
from config.settings import Settings
from .logger import log_debug, log_error, log_info


class DataManager:
    """Gestiona todos los archivos y base de datos del bot."""
    
    DB_PATH: str = Settings.DB_PATH
    
    @staticmethod
    @contextmanager
    def get_db_connection():
        """Context manager para conexiones SQLite."""
        Settings.crear_directorios()
        conn = sqlite3.connect(DataManager.DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            log_error(f"Error DB: {e}")
            raise
        finally:
            conn.close()
    
    @staticmethod
    def inicializar_db():
        """Crea las tablas necesarias en SQLite."""
        with DataManager.get_db_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS procesados (
                    partido_id TEXT PRIMARY KEY,
                    fecha_procesamiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS predicciones (
                    partido_id TEXT PRIMARY KEY,
                    partido_str TEXT,
                    analisis TEXT,
                    fecha DATE,
                    estado TEXT DEFAULT 'pendiente'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS historial (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partido_str TEXT,
                    marcador TEXT,
                    auditoria TEXT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metricas (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    picks_totales INTEGER DEFAULT 0,
                    picks_aprobados INTEGER DEFAULT 0,
                    picks_descartados INTEGER DEFAULT 0,
                    apuestas_ganadas INTEGER DEFAULT 0,
                    apuestas_perdidas INTEGER DEFAULT 0,
                    errores_api INTEGER DEFAULT 0,
                    ultima_ejecucion TIMESTAMP
                )
            """)
            # Insertar fila inicial si no existe
            conn.execute("""
                INSERT OR IGNORE INTO metricas (id) VALUES (1)
            """)
        log_info("✅ Base de datos inicializada")
    
    # ========================================================================
    # MÉTODOS PARA PROCESADOS
    # ========================================================================
    
    @staticmethod
    def cargar_procesados() -> List[str]:
        """Carga la lista de partidos ya procesados."""
        try:
            with DataManager.get_db_connection() as conn:
                cursor = conn.execute("SELECT partido_id FROM procesados ORDER BY fecha_procesamiento DESC")
                return [row["partido_id"] for row in cursor.fetchall()]
        except Exception as e:
            log_error(f"Error al cargar procesados: {e}")
            return []
    
    @staticmethod
    def guardar_procesado(partido_id: str):
        """Marca un partido como procesado."""
        try:
            with DataManager.get_db_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO procesados (partido_id) VALUES (?)",
                    (partido_id,)
                )
            log_debug(f"Procesado guardado: {partido_id}")
        except Exception as e:
            log_error(f"Error al guardar procesado: {e}")
    
    # ========================================================================
    # MÉTODOS PARA PREDICCIONES
    # ========================================================================
    
    @staticmethod
    def cargar_predicciones_pendientes() -> Dict[str, dict]:
        """Carga las predicciones pendientes de auditoría."""
        try:
            with DataManager.get_db_connection() as conn:
                cursor = conn.execute(
                    "SELECT partido_id, partido_str, analisis, fecha FROM predicciones WHERE estado = 'pendiente'"
                )
                pendientes = {}
                for row in cursor.fetchall():
                    pendientes[row["partido_id"]] = {
                        "partido_str": row["partido_str"],
                        "analisis": row["analisis"],
                        "fecha": row["fecha"]
                    }
                return pendientes
        except Exception as e:
            log_error(f"Error al cargar predicciones pendientes: {e}")
            return {}
    
    @staticmethod
    def guardar_prediccion_pendiente(partido_id: str, partido_str: str, analisis: str):
        """Guarda una predicción para auditoría futura."""
        try:
            with DataManager.get_db_connection() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO predicciones 
                       (partido_id, partido_str, analisis, fecha, estado) 
                       VALUES (?, ?, ?, ?, 'pendiente')""",
                    (partido_id, partido_str, analisis, datetime.today().strftime('%Y-%m-%d'))
                )
            log_debug(f"Predicción pendiente guardada: {partido_id}")
        except Exception as e:
            log_error(f"Error al guardar predicción pendiente: {e}")
    
    @staticmethod
    def actualizar_prediccion_estado(partido_id: str, estado: str):
        """Actualiza el estado de una predicción."""
        try:
            with DataManager.get_db_connection() as conn:
                conn.execute(
                    "UPDATE predicciones SET estado = ? WHERE partido_id = ?",
                    (estado, partido_id)
                )
        except Exception as e:
            log_error(f"Error al actualizar estado de predicción: {e}")
    
    @staticmethod
    def eliminar_prediccion(partido_id: str):
        """Elimina una predicción después de auditar."""
        try:
            with DataManager.get_db_connection() as conn:
                conn.execute("DELETE FROM predicciones WHERE partido_id = ?", (partido_id,))
        except Exception as e:
            log_error(f"Error al eliminar predicción: {e}")
    
    # ========================================================================
    # MÉTODOS PARA HISTORIAL
    # ========================================================================
    
    @staticmethod
    def leer_aprendizaje() -> str:
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
    def guardar_aprendizaje(contenido: str):
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
    def agregar_a_aprendizaje(nuevas_reglas: List[str]):
        """Agrega nuevas reglas al archivo de aprendizaje."""
        try:
            Settings.crear_directorios()
            ruta = Settings.FILES["aprendizaje"]
            with open(ruta, "a", encoding="utf-8") as f:
                f.write(f"\n### NUEVAS REGLAS AUTOMÁTICAS - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                for regla in nuevas_reglas:
                    f.write(f"- {regla}\n")
            log_debug(f"Se agregaron {len(nuevas_reglas)} nuevas reglas")
        except Exception as e:
            log_error(f"Error al agregar reglas: {e}")
    
    @staticmethod
    def agregar_historial_resultado(partido_str: str, marcador: str, auditoria: str):
        """Agrega un resultado auditado al historial en DB."""
        try:
            with DataManager.get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO historial (partido_str, marcador, auditoria) VALUES (?, ?, ?)",
                    (partido_str, marcador, auditoria)
                )
            
            # También mantener archivo legacy
            ruta = Settings.FILES["historial"]
            with open(ruta, "a", encoding="utf-8") as f:
                f.write(f"\n--- AUDITORÍA ---\nPartido: {marcador}\n{auditoria}")
            
            log_debug(f"Historial actualizado")
        except Exception as e:
            log_error(f"Error al agregar al historial: {e}")
    
    # ========================================================================
    # MÉTODOS PARA MÉTRICAS
    # ========================================================================
    
    @staticmethod
    def obtener_metricas() -> Dict[str, Any]:
        """Obtiene las métricas actuales del bot."""
        try:
            with DataManager.get_db_connection() as conn:
                cursor = conn.execute("SELECT * FROM metricas WHERE id = 1")
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return {}
        except Exception as e:
            log_error(f"Error al obtener métricas: {e}")
            return {}
    
    @staticmethod
    def actualizar_metricas(picks_totales: int = None, picks_aprobados: int = None,
                           picks_descartados: int = None, apuestas_ganadas: int = None,
                           apuestas_perdidas: int = None, errores_api: int = None):
        """Actualiza las métricas del bot."""
        try:
            with DataManager.get_db_connection() as conn:
                updates = []
                values = []
                
                if picks_totales is not None:
                    updates.append("picks_totales = ?")
                    values.append(picks_totales)
                if picks_aprobados is not None:
                    updates.append("picks_aprobados = ?")
                    values.append(picks_aprobados)
                if picks_descartados is not None:
                    updates.append("picks_descartados = ?")
                    values.append(picks_descartados)
                if apuestas_ganadas is not None:
                    updates.append("apuestas_ganadas = ?")
                    values.append(apuestas_ganadas)
                if apuestas_perdidas is not None:
                    updates.append("apuestas_perdidas = ?")
                    values.append(apuestas_perdidas)
                if errores_api is not None:
                    updates.append("errores_api = ?")
                    values.append(errores_api)
                
                updates.append("ultima_ejecucion = ?")
                values.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                
                values.append(1)  # id = 1
                
                query = f"UPDATE metricas SET {', '.join(updates)} WHERE id = ?"
                conn.execute(query, values)
        except Exception as e:
            log_error(f"Error al actualizar métricas: {e}")
    
    @staticmethod
    def calcular_roi() -> float:
        """Calcula el ROI aproximado del bot."""
        metricas = DataManager.obtener_metricas()
        total = metricas.get("apuestas_ganadas", 0) + metricas.get("apuestas_perdidas", 0)
        if total == 0:
            return 0.0
        return ((metricas.get("apuestas_ganadas", 0) - metricas.get("apuestas_perdidas", 0)) / total) * 100
