"""Extractor de características para Machine Learning"""
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from utils.logger import log_info, log_error, log_debug


class FeatureExtractor:
    """Extrae características numéricas de partidos para ML."""
    
    # Mapa de deportes a características específicas
    SPORT_FEATURES = {
        "soccer": ["xg_home", "xg_away", "ppda_home", "ppda_away", "home_advantage"],
        "basketball": ["pace", "ortg_home", "ortg_away", "drtg_home", "drtg_away", "rest_days"],
        "baseball": ["era_home", "era_away", "whip_home", "whip_away", "ops_home", "ops_away"]
    }
    
    @staticmethod
    def extraer_caracteristicas_basicas(partido_str: str) -> Dict[str, float]:
        """Extrae características básicas del string del partido."""
        features = {}
        
        # Hash del partido para consistencia
        features["partido_hash"] = float(hashlib.md5(partido_str.encode()).hexdigest()[:8], 16) / (16**8)
        
        # Detectar deporte
        if "NBA" in partido_str.upper() or "BASKETBALL" in partido_str.upper():
            features["es_basketball"] = 1.0
            features["es_futbol"] = 0.0
            features["es_baseball"] = 0.0
        elif "MLB" in partido_str.upper() or "BASEBALL" in partido_str.upper():
            features["es_basketball"] = 0.0
            features["es_futbol"] = 0.0
            features["es_baseball"] = 1.0
        else:  # Soccer por defecto
            features["es_basketball"] = 0.0
            features["es_futbol"] = 1.0
            features["es_baseball"] = 0.0
        
        # Ventaja de localía (estimada)
        features["home_advantage"] = 0.15  # Valor base
        
        # Hora del partido (normalizada 0-1)
        hora = datetime.now().hour
        features["hora_normalizada"] = hora / 24.0
        
        # Día de la semana (normalizada)
        dia_semana = datetime.now().weekday()
        features["dia_semana"] = dia_semana / 7.0
        
        log_debug(f"Características básicas extraídas: {len(features)} features")
        return features
    
    @staticmethod
    def extraer_caracteristicas_historial(historial: str, partido_str: str) -> Dict[str, float]:
        """Extrae características del historial de aprendizaje."""
        features = {}
        
        # Contar reglas activas
        reglas_count = historial.count("REGLA:") + historial.count("- [")
        features["reglas_activas_count"] = min(reglas_count / 100.0, 1.0)  # Normalizar a 0-1
        
        # Detectar patrones en historial
        features["tiene_reglas_defensa"] = 1.0 if "DEFENSA" in historial.upper() else 0.0
        features["tiene_reglas_ataque"] = 1.0 if "ATAQUE" in historial.upper() else 0.0
        features["tiene_reglas_localia"] = 1.0 if "LOCAL" in historial.upper() or "HOME" in historial.upper() else 0.0
        
        # Edad del historial (número de líneas)
        lineas_count = len(historial.split("\n"))
        features["historial_size"] = min(lineas_count / 1000.0, 1.0)
        
        log_debug(f"Características de historial extraídas: {len(features)} features")
        return features
    
    @staticmethod
    def extraer_caracteristicas_analisis(analisis: str) -> Dict[str, float]:
        """Extrae características del análisis de IA."""
        features = {}
        
        if not analisis:
            return features
        
        # Extraer probabilidad mencionada
        prob_match = re.search(r'PROBABILIDAD REAL[:\s]*([0-9]+)%', analisis, re.IGNORECASE)
        if prob_match:
            features["probabilidad_ia"] = float(prob_match.group(1)) / 100.0
        else:
            features["probabilidad_ia"] = 0.5  # Default
        
        # Extraer cuota mínima
        cuota_match = re.search(r'CUOTA MÍNIMA[:\s]*([0-9.]+)', analisis, re.IGNORECASE)
        if cuota_match:
            features["cuota_minima"] = float(cuota_match.group(1)) / 10.0  # Normalizar
        else:
            features["cuota_minima"] = 2.0
        
        # Detectar veredicto
        features["veredicto_aprobado"] = 1.0 if "APROBADO" in analisis.upper() else 0.0
        features["veredicto_descartado"] = 1.0 if "DESCARTADO" in analisis.upper() else 0.0
        
        # Longitud del análisis (indicador de confianza)
        features["analisis_length"] = min(len(analisis) / 1000.0, 1.0)
        
        # Contar elementos técnicos mencionados
        tecnicos = ["xG", "PPDA", "ERA", "WHIP", "OPS", "PACE", "ORTG", "DRTG"]
        features["tecnicos_mencionados"] = sum(1 for t in tecnicos if t in analisis.upper()) / len(tecnicos)
        
        log_debug(f"Características de análisis extraídas: {len(features)} features")
        return features
    
    @staticmethod
    def crear_vector_caracteristicas(
        partido_str: str,
        historial: str,
        analisis: str,
        resultado: Optional[str] = None
    ) -> Dict[str, Any]:
        """Crea un vector completo de características para ML."""
        
        features = {}
        
        # Características básicas
        features.update(FeatureExtractor.extraer_caracteristicas_basicas(partido_str))
        
        # Características de historial
        features.update(FeatureExtractor.extraer_caracteristicas_historial(historial, partido_str))
        
        # Características de análisis
        features.update(FeatureExtractor.extraer_caracteristicas_analisis(analisis))
        
        # Label (si hay resultado)
        if resultado:
            features["label_ganada"] = 1.0 if "GANADA" in resultado.upper() else 0.0
            features["label_perdida"] = 1.0 if "PERDIDA" in resultado.upper() else 0.0
        
        features["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        features["partido_str"] = partido_str
        features["analisis"] = analisis
        
        return features
    
    @staticmethod
    def convertir_a_array_ml(features: Dict[str, Any]) -> List[float]:
        """Convierte diccionario de features a array numérico para ML."""
        feature_names = [
            "partido_hash",
            "es_basketball",
            "es_futbol",
            "es_baseball",
            "home_advantage",
            "hora_normalizada",
            "dia_semana",
            "reglas_activas_count",
            "tiene_reglas_defensa",
            "tiene_reglas_ataque",
            "tiene_reglas_localia",
            "historial_size",
            "probabilidad_ia",
            "cuota_minima",
            "veredicto_aprobado",
            "veredicto_descartado",
            "analisis_length",
            "tecnicos_mencionados"
        ]
        
        return [features.get(name, 0.0) for name in feature_names]
