"""Sistema de auditoría y aprendizaje ML para EdgeBot-IA-V2"""
from typing import List, Dict
from utils.logger import log_info, log_error, log_debug
from utils.data_manager import DataManager
from utils.api_client import ESPNClient, GroqClient, TelegramClient
from config.settings import Settings
from core.ml_model import MLModel
from utils.feature_extractor import FeatureExtractor


class AuditManager:
    """Gestiona la auditoría de predicciones y entrenamiento ML."""
    
    def __init__(self):
        """Inicializa el AuditManager."""
        if not Settings.inicializar():
            raise ValueError("Configuración inválida. Revisa las variables de entorno.")
        DataManager.inicializar_db()
        
        # 🆕 Inicializar modelo ML
        self.ml_model = MLModel()
        self.ml_model.cargar_modelo()
        
        log_info("AuditManager inicializado con ML")
    
    def obtener_resultados_finalizados(self) -> List[tuple]:
        """Obtiene resultados de partidos finalizados."""
        log_info("Obteniendo resultados finalizados...")
        return ESPNClient.obtener_resultados_finalizados()
    
    def auditar_predicciones(self):
        """Audita las predicciones y entrena el modelo ML."""
        log_info("Iniciando auditoría de predicciones...")
        
        pendientes = DataManager.cargar_predicciones_pendientes()
        if not pendientes:
            log_info("No hay predicciones pendientes para auditar")
            return
        
        resultados = self.obtener_resultados_finalizados()
        claves_a_borrar: List[str] = []
        nuevas_reglas: List[str] = []
        metricas = DataManager.obtener_metricas()
        
        muestras_ml_agregadas = 0
        necesita_reentrenamiento = False
        
        for resultado in resultados:
            home, away, marcador = resultado
            
            for p_id, p_data in pendientes.items():
                if home in p_data["partido_str"] and away in p_data["partido_str"]:
                    log_info(f"Auditando: {marcador}")
                    
                    try:
                        auditoria = GroqClient.auditar_resultado(
                            p_data["partido_str"],
                            p_data["analisis"],
                            marcador
                        )
                        
                        if auditoria:
                            # Determinar si ganó o perdió
                            es_ganada = "GANADA" in auditoria.upper()
                            
                            if es_ganada:
                                DataManager.actualizar_metricas(
                                    apuestas_ganadas=metricas.get("apuestas_ganadas", 0) + 1
                                )
                            else:
                                DataManager.actualizar_metricas(
                                    apuestas_perdidas=metricas.get("apuestas_perdidas", 0) + 1
                                )
                            
                            # 🆕 Extraer features ML y agregar muestra de entrenamiento
                            features = FeatureExtractor.crear_vector_caracteristicas(
                                partido_str=p_data["partido_str"],
                                historial=DataManager.leer_aprendizaje(),
                                analisis=p_data["analisis"],
                                resultado=auditoria
                            )
                            
                            label = 1 if es_ganada else 0
                            
                            # Agregar a dataset de entrenamiento ML
                            if self.ml_model.agregar_muestra_entrenamiento(features, auditoria):
                                muestras_ml_agregadas += 1
                                necesita_reentrenamiento = True
                            
                            # Guardar en historial DB
                            DataManager.agregar_historial_resultado(
                                p_data["partido_str"],
                                marcador,
                                auditoria,
                                features
                            )
                            
                            # Extraer reglas para sistema híbrido
                            for linea in auditoria.split("\n"):
                                if "REGLA:" in linea.upper():
                                    regla = linea.replace('REGLA:', '').strip()
                                    nuevas_reglas.append(regla)
                    
                    except Exception as e:
                        log_error(f"Error auditando {p_id}: {e}")
                    
                    claves_a_borrar.append(p_id)
        
        # Actualizar predicciones pendientes
        for clave in claves_a_borrar:
            DataManager.eliminar_prediccion(clave)
        
        # Inyectar nuevas reglas
        if nuevas_reglas:
            DataManager.agregar_a_aprendizaje(nuevas_reglas)
            log_info(f"✅ Se inyectaron {len(nuevas_reglas)} nuevas reglas")
        
        # 🆕 Reentrenar modelo ML si es necesario
        if necesita_reentrenamiento:
            log_info("🔄 Reentrenando modelo ML con nuevas muestras...")
            if self.ml_model.entrenar_modelo():
                # Actualizar métricas ML
                importancia = self.ml_model.obtener_importancia_caracteristicas()
                log_info(f"📊 Feature más importante: {max(importancia, key=importancia.get) if importancia else 'N/A'}")
                
                mensaje = f"""🎓 𝗔𝗖𝗧𝗨𝗔𝗟𝗜𝗭𝗔𝗖𝗜Ó𝗡 𝗗𝗘 𝗠𝗢𝗗𝗘𝗟𝗢 𝗠𝗟
━━━━━━━━━━━━━━━━━━━━
✅ {muestras_ml_agregadas} nuevas muestras procesadas
✅ Modelo reentrenado exitosamente
✅ {len(nuevas_reglas)} reglas aprendidas

📊 ROI Actual: {DataManager.calcular_roi():.2f}%
━━━━━━━━━━━━━━━━━━━━
El bot mejora cada día con tus resultados!"""
                TelegramClient.enviar_mensaje(mensaje)
            else:
                log_info("⚠️ Reentrenamiento no ejecutado (insuficientes muestras)")
        else:
            log_info("No se generaron nuevas reglas en este ciclo")
    
    def ejecutar(self):
        """Ejecuta el ciclo completo de auditoría."""
        log_info("=" * 50)
        log_info("Iniciando Auditoría y Entrenamiento ML")
        log_info("=" * 50)
        
        try:
            self.auditar_predicciones()
            log_info("Auditoría completada exitosamente")
        except Exception as e:
            log_error(f"Error durante auditoría: {e}")
            raise
        
        log_info("=" * 50)
