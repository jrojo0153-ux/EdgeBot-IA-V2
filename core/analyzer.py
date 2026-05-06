"""Motor de análisis principal de EdgeBot-IA-V2 con ML"""
from datetime import datetime
from dataclasses import dataclass
from typing import List, Tuple, Optional
from utils.logger import log_info, log_error, log_debug
from utils.data_manager import DataManager
from utils.api_client import ESPNClient, GroqClient, TelegramClient
from config.settings import Settings
from core.ml_model import MLModel
from utils.feature_extractor import FeatureExtractor
import time


@dataclass
class AnalysisPick:
    """Representa un pick analizado."""
    partido_id: str
    partido_str: str
    analisis: str
    aprobado: bool
    ml_probabilidad: float = 0.5
    ml_confianza: float = 0.5
    fuente_decision: str = "IA"


class EdgeBotAnalyzer:
    """Motor principal de análisis del bot con ML."""
    
    def __init__(self):
        """Inicializa el analyzer con validación de configuración."""
        if not Settings.inicializar():
            raise ValueError("Configuración inválida. Revisa las variables de entorno.")
        
        DataManager.inicializar_db()
        self.procesados = DataManager.cargar_procesados()
        self.historial = DataManager.leer_aprendizaje()
        
        # 🆕 Inicializar modelo ML
        self.ml_model = MLModel()
        self.ml_model.cargar_modelo()
        
        log_info("EdgeBotAnalyzer inicializado con ML")
    
    def obtener_partidos_nuevos(self) -> List[Tuple[str, str]]:
        """Obtiene partidos nuevos sin procesar."""
        log_info("Buscando partidos nuevos sin procesar...")
        partidos_espn = ESPNClient.obtener_partidos_por_jugar()
        hoy = datetime.today().strftime('%Y-%m-%d')
        
        partidos_nuevos: List[Tuple[str, str]] = []
        for liga_key, home, away, partido_str, liga in partidos_espn:
            partido_id = f"{hoy}_{partido_str}"
            if partido_id not in self.procesados:
                partidos_nuevos.append((partido_id, partido_str))
        
        log_info(f"Encontrados {len(partidos_nuevos)} partidos nuevos")
        return partidos_nuevos[:Settings.MAX_PICKS_PER_RUN]
    
    def analizar_partido(self, partido_id: str, partido_str: str) -> Optional[AnalysisPick]:
        """Analiza un partido con IA + ML."""
        log_info(f"Analizando: {partido_str}")
        
        try:
            # Análisis con IA
            analisis = GroqClient.analizar_partido(self.historial, partido_str)
            
            if not analisis:
                log_error(f"No se pudo analizar: {partido_str}")
                metricas = DataManager.obtener_metricas()
                DataManager.actualizar_metricas(
                    errores_api=metricas.get("errores_api", 0) + 1
                )
                return None
            
            # 🆕 Extraer características para ML
            features = FeatureExtractor.crear_vector_caracteristicas(
                partido_str=partido_str,
                historial=self.historial,
                analisis=analisis
            )
            
            # 🆕 Predicción ML
            ml_prob, ml_conf, ml_recomendacion = self.ml_model.predecir(features)
            
            # Decisión combinada (IA + ML)
            aprobado_ia = "APROBADO" in analisis.upper()
            aprobado_ml = ml_recomendacion == "APROBADO_ML"
            
            # Si ML está entrenado, dar peso 60% a ML, 40% a IA
            if self.ml_model.is_trained:
                aprobado = aprobado_ml or (aprobado_ia and ml_conf > 0.6)
                fuente = "ML_IA_HYBRID"
            else:
                aprobado = aprobado_ia
                fuente = "IA_PURE"
            
            pick = AnalysisPick(
                partido_id=partido_id,
                partido_str=partido_str,
                analisis=analisis,
                aprobado=aprobado,
                ml_probabilidad=ml_prob,
                ml_confianza=ml_conf,
                fuente_decision=fuente
            )
            
            log_debug(f"Pick {'APROBADO' if aprobado else 'DESCARTADO'} | ML: {ml_prob:.2%} | Fuente: {fuente}")
            return pick
            
        except Exception as e:
            log_error(f"Error al analizar partido {partido_str}: {e}")
            return None
    
    def procesar_picks(self, picks: List[AnalysisPick]):
        """Procesa los picks aprobados."""
        metricas = DataManager.obtener_metricas()
        
        for pick in picks:
            log_info(f"Procesando: {pick.partido_str}")
            
            # Actualizar métricas
            DataManager.actualizar_metricas(
                picks_totales=metricas.get("picks_totales", 0) + 1,
                picks_aprobados=metricas.get("picks_aprobados", 0) + 1 if pick.aprobado else None,
                picks_descartados=metricas.get("picks_descartados", 0) + 1 if not pick.aprobado else None
            )
            
            # Marcar como procesado
            DataManager.guardar_procesado(pick.partido_id)
            
            if pick.aprobado:
                # Guardar para auditoría futura con datos ML
                DataManager.guardar_prediccion_pendiente(
                    pick.partido_id,
                    pick.partido_str,
                    pick.analisis,
                    pick.ml_probabilidad,
                    pick.ml_confianza
                )
                
                # Enviar a Telegram con info ML
                mensaje = f"""🤖 𝗘𝗗𝗚𝗘 𝗕𝗢𝗧 𝗣𝗥𝗢 (𝗠𝗟 𝗘𝗡𝗛𝗔𝗡𝗖𝗘𝗗)
━━━━━━━━━━━━━━━━━━━━
⚽ 𝗣𝗔𝗥𝗧𝗜𝗗𝗢:
{pick.partido_str}

{pick.analisis}

🧠 𝗠𝗟 𝗔𝗡𝗔𝗟𝗬𝗧𝗜𝗖𝗦:
• Probabilidad: {pick.ml_probabilidad:.1%}
• Confianza: {pick.ml_confianza:.1%}
• Fuente: {pick.fuente_decision}
━━━━━━━━━━━━━━━━━━━━
📊 ROI Actual: {DataManager.calcular_roi():.2f}%"""
                
                TelegramClient.enviar_mensaje(mensaje)
                log_info(f"✅ Pick aprobado y enviado a Telegram")
            else:
                resumen_ia = pick.analisis.replace('\n', ' | ')[:200]
                log_info(f"❌ Pick descartado | ML: {pick.ml_probabilidad:.1%} | Motivo: {resumen_ia}...")
            
            time.sleep(Settings.DELAY_BETWEEN_PICKS)
    
    def ejecutar(self):
        """Ejecuta el ciclo completo del bot."""
        log_info("=" * 50)
        log_info("Iniciando Edge Bot Pro ML (Escaneo Horario)")
        log_info("=" * 50)
        
        try:
            # Mostrar estado del modelo ML
            if self.ml_model.is_trained:
                log_info(f"✅ Modelo ML cargado y activo")
            else:
                log_info(f"⚠️ Modelo ML no entrenado, usando IA pura")
            
            partidos = self.obtener_partidos_nuevos()
            
            if not partidos:
                log_info("No hay partidos nuevos sin procesar en esta hora")
                return
            
            picks: List[AnalysisPick] = []
            for partido_id, partido_str in partidos:
                pick = self.analizar_partido(partido_id, partido_str)
                if pick:
                    picks.append(pick)
            
            if picks:
                self.procesar_picks(picks)
            
            log_info("=" * 50)
            log_info("Escaneo finalizado")
            log_info("=" * 50)
            
            # Mostrar resumen de métricas
            metricas = DataManager.obtener_metricas()
            log_info(f"📊 MÉTRICAS: Totales={metricas.get('picks_totales', 0)} | "
                    f"Aprobados={metricas.get('picks_aprobados', 0)} | "
                    f"ROI={DataManager.calcular_roi():.2f}% | "
                    f"ML Activo={self.ml_model.is_trained}")
            
        except Exception as e:
            log_error(f"Error crítico en ejecución: {e}")
            raise
