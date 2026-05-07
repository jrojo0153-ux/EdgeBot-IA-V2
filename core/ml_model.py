"""Gestor centralizado de datos para EdgeBot-IA-V2 con SQLite y ML"""
import os
import json
import sqlite3
import csv
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import contextmanager
from config.settings import Settings
from utils.logger import log_debug, log_error, log_info


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
                    party_id TEXT PRIMARY KEY,
                    partido_str TEXT,
                    analisis TEXT,
                    fecha DATE,
                    estado TEXT DEFAULT 'pendiente',
                    ml_probabilidad REAL,
                    ml_confianza REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS historial (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partido_str TEXT,
                    marcador TEXT,
                    auditoria TEXT,
                    ml_features TEXT,
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
                    ml_accuracy REAL DEFAULT 0.0,
                    ml_precision REAL DEFAULT 0.0,
                    ultima_ejecucion TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entrenamiento_ml (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    features TEXT,
                    label INTEGER,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                INSERT OR IGNORE INTO metricas (id) VALUES (1)
            """)
        log_info("✅ Base de datos inicializada")
    
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
    
    @staticmethod
    def cargar_predicciones_pendientes() -> Dict[str, dict]:
        """Carga las predicciones pendientes de auditoría."""
        try:
            with DataManager.get_db_connection() as conn:
                cursor = conn.execute(
                    "SELECT partido_id, partido_str, analisis, fecha, ml_probabilidad, ml_confianza FROM predicciones WHERE estado = 'pendiente'"
                )
                pendientes = {}
                for row in cursor.fetchall():
                    pendientes[row["partido_id"]] = {
                        "partido_str": row["partido_str"],
                        "analisis": row["analisis"],
                        "fecha": row["fecha"],
                        "ml_probabilidad": row["ml_probabilidad"],
                        "ml_confianza": row["ml_confianza"]
                    }
                return pendientes
        except Exception as e:
            log_error(f"Error al cargar predicciones pendientes: {e}")
            return {}
    
    @staticmethod
    def guardar_prediccion_pendiente(partido_id: str, partido_str: str, analisis: str, 
                                     ml_prob: float = None, ml_conf: float = None):
        """Guarda una predicción para auditoría futura."""
        try:
            with DataManager.get_db_connection() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO predicciones 
                       (partido_id, partido_str, analisis, fecha, estado, ml_probabilidad, ml_confianza) 
                       VALUES (?, ?, ?, ?, 'pendiente', ?, ?)""",
                    (partido_id, partido_str, analisis, datetime.today().strftime('%Y-%m-%d'), 
                     ml_prob, ml_conf)
                )
            log_debug(f"Predicción pendiente guardada: {partido_id}")
        except Exception as e:
            log_error(f"Error al guardar predicción pendiente: {e}")
    
    @staticmethod
    def eliminar_prediccion(partido_id: str):
        """Elimina una predicción después de auditar."""
        try:
            with DataManager.get_db_connection() as conn:
                conn.execute("DELETE FROM predicciones WHERE partido_id = ?", (partido_id,))
        except Exception as e:
            log_error(f"Error al eliminar predicción: {e}")
    
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
    def agregar_historial_resultado(partido_str: str, marcador: str, auditoria: str, 
                                    ml_features: Dict = None):
        """Agrega un resultado auditado al historial en DB."""
        try:
            with DataManager.get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO historial (partido_str, marcador, auditoria, ml_features) VALUES (?, ?, ?, ?)",
                    (partido_str, marcador, auditoria, json.dumps(ml_features) if ml_features else None)
                )
            
            log_debug(f"Historial actualizado")
        except Exception as e:
            log_error(f"Error al agregar al historial: {e}")
    
    @staticmethod
    def guardar_muestra_ml(features: Dict, label: int):
        """Guarda una muestra para entrenamiento ML."""
        try:
            with DataManager.get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO entrenamiento_ml (features, label) VALUES (?, ?)",
                    (json.dumps(features), label)
                )
            log_debug(f"Muestra ML guardada: label={label}")
        except Exception as e:
            log_error(f"Error al guardar muestra ML: {e}")
    
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
                           apuestas_perdidas: int = None, errores_api: int = None,
                           ml_accuracy: float = None, ml_precision: float = None):
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
                if ml_accuracy is not None:
                    updates.append("ml_accuracy = ?")
                    values.append(ml_accuracy)
                if ml_precision is not None:
                    updates.append("ml_precision = ?")
                    values.append(ml_precision)
                
                updates.append("ultima_ejecucion = ?")
                values.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                
                values.append(1)
                
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
