"""Modelo de Machine Learning para EdgeBot-IA-V2"""
import os
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
from utils.logger import log_info, log_error, log_debug
from config.settings import Settings
from utils.feature_extractor import FeatureExtractor
from utils.data_manager import DataManager


class MLModel:
    """Modelo de ML que aprende de predicciones diarias."""
    
    def __init__(self):
        """Inicializa el modelo de ML."""
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = Settings.ML_MODEL_PATH
        self.training_data_path = Settings.ML_TRAINING_DATA_PATH
        self.is_trained = False
        
        # Feature names para consistencia
        self.feature_names = [
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
        
    def cargar_datos_entrenamiento(self) -> Optional[pd.DataFrame]:
        """Carga datos de entrenamiento desde CSV."""
        try:
            if os.path.exists(self.training_data_path):
                df = pd.read_csv(self.training_data_path)
                log_info(f"✅ Cargados {len(df)} registros de entrenamiento")
                return df
            else:
                log_info("⚠️ No existe archivo de entrenamiento, creando nuevo")
                return pd.DataFrame()
        except Exception as e:
            log_error(f"Error cargando datos de entrenamiento: {e}")
            return pd.DataFrame()
    
    def guardar_datos_entrenamiento(self, df: pd.DataFrame):
        """Guarda datos de entrenamiento en CSV."""
        try:
            Settings.crear_directorios()
            df.to_csv(self.training_data_path, index=False)
            log_info(f"✅ Guardados {len(df)} registros en {self.training_data_path}")
        except Exception as e:
            log_error(f"Error guardando datos de entrenamiento: {e}")
    
    def agregar_muestra_entrenamiento(self, features: Dict[str, Any], resultado: str):
        """Agrega una nueva muestra al dataset de entrenamiento."""
        try:
            df = self.cargar_datos_entrenamiento()
            
            # Crear nueva fila
            nueva_fila = {}
            for feature in self.feature_names:
                nueva_fila[feature] = features.get(feature, 0.0)
            
            # Label
            nueva_fila["label"] = 1.0 if "GANADA" in resultado.upper() else 0.0
            nueva_fila["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Agregar al DataFrame
            df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
            
            # Guardar
            self.guardar_datos_entrenamiento(df)
            
            log_info(f"✅ Muestra agregada. Total: {len(df)} registros")
            
            # Verificar si necesita reentrenamiento
            if len(df) >= Settings.ML_MIN_SAMPLES_FOR_TRAINING:
                muestras_desde_ultimo = len(df) % Settings.ML_RETRAIN_THRESHOLD
                if muestras_desde_ultimo == 0:
                    log_info("🔄 Umbral de reentrenamiento alcanzado")
                    return True
            
            return False
            
        except Exception as e:
            log_error(f"Error agregando muestra: {e}")
            return False
    
    def entrenar_modelo(self) -> bool:
        """Entrena o reentrena el modelo de ML."""
        try:
            log_info("=" * 50)
            log_info("Iniciando entrenamiento de modelo ML")
            log_info("=" * 50)
            
            df = self.cargar_datos_entrenamiento()
            
            if len(df) < Settings.ML_MIN_SAMPLES_FOR_TRAINING:
                log_info(f"⚠️ Insuficientes muestras ({len(df)} < {Settings.ML_MIN_SAMPLES_FOR_TRAINING})")
                return False
            
            # Preparar datos
            X = df[self.feature_names].values
            y = df["label"].values
            
            # Normalizar características
            X_scaled = self.scaler.fit_transform(X)
            
            # Split train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, stratify=y if len(set(y)) > 1 else None
            )
            
            # Crear modelo (Random Forest con Gradient Boosting ensemble)
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42,
                min_samples_split=5,
                min_samples_leaf=2
            )
            
            # Entrenar
            log_info("Entrenando modelo...")
            self.model.fit(X_train, y_train)
            
            # Validar
            y_pred = self.model.predict(X_test)
            
            if len(set(y_test)) > 1:
                accuracy = accuracy_score(y_test, y_pred)
                precision = precision_score(y_test, y_pred, zero_division=0)
                recall = recall_score(y_test, y_pred, zero_division=0)
                f1 = f1_score(y_test, y_pred, zero_division=0)
                
                log_info(f"📊 MÉTRICAS DE VALIDACIÓN:")
                log_info(f"   Accuracy:  {accuracy:.2%}")
                log_info(f"   Precision: {precision:.2%}")
                log_info(f"   Recall:    {recall:.2%}")
                log_info(f"   F1-Score:  {f1:.2%}")
                
                # Cross-validation
                cv_scores = cross_val_score(self.model, X_scaled, y, cv=5)
                log_info(f"   CV Score:  {cv_scores.mean():.2%} (+/- {cv_scores.std() * 2:.2%})")
            else:
                log_info("⚠️ Datos desbalanceados, métricas limitadas")
            
            # Guardar modelo
            self.guardar_modelo()
            self.is_trained = True
            
            log_info("✅ Modelo entrenado y guardado exitosamente")
            log_info("=" * 50)
            
            return True
            
        except Exception as e:
            log_error(f"Error entrenando modelo: {e}")
            import traceback
            log_error(traceback.format_exc())
            return False
    
    def guardar_modelo(self):
        """Guarda el modelo en disco."""
        try:
            Settings.crear_directorios()
            
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'trained_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(self.model_path, 'wb') as f:
                joblib.dump(model_data, f)
            
            log_info(f"✅ Modelo guardado en {self.model_path}")
            
        except Exception as e:
            log_error(f"Error guardando modelo: {e}")
    
    def cargar_modelo(self) -> bool:
        """Carga el modelo desde disco."""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    model_data = joblib.load(f)
                
                self.model = model_data['model']
                self.scaler = model_data['scaler']
                self.feature_names = model_data.get('feature_names', self.feature_names)
                self.is_trained = True
                
                log_info(f"✅ Modelo cargado desde {self.model_path}")
                return True
            else:
                log_info("⚠️ No existe modelo guardado, se usará IA pura")
                return False
                
        except Exception as e:
            log_error(f"Error cargando modelo: {e}")
            return False
    
    def predecir(self, features: Dict[str, Any]) -> Tuple[float, float, str]:
        """
        Predice resultado usando el modelo ML.
        Returns: (probabilidad_ganada, confianza, recomendacion)
        """
        try:
            if not self.is_trained or self.model is None:
                # Fallback a probabilidad de IA
                prob_ia = features.get("probabilidad_ia", 0.5)
                return prob_ia, 0.5, "IA_PURE"
            
            # Convertir features a array
            X = np.array([FeatureExtractor.convertir_a_array_ml(features)])
            X_scaled = self.scaler.transform(X)
            
            # Predecir probabilidad
            prob_ganada = self.model.predict_proba(X_scaled)[0][1]
            confianza = max(prob_ganada, 1 - prob_ganada)
            
            # Determinar recomendación
            if prob_ganada >= Settings.ML_CONFIDENCE_THRESHOLD:
                recomendacion = "APROBADO_ML"
            elif prob_ganada <= (1 - Settings.ML_CONFIDENCE_THRESHOLD):
                recomendacion = "DESCARTADO_ML"
            else:
                recomendacion = "INCERTO_ML"
            
            log_debug(f"Predicción ML: {prob_ganada:.2%} | Confianza: {confianza:.2%} | {recomendacion}")
            
            return prob_ganada, confianza, recomendacion
            
        except Exception as e:
            log_error(f"Error en predicción ML: {e}")
            return 0.5, 0.5, "ERROR_ML"
    
    def obtener_importancia_caracteristicas(self) -> Dict[str, float]:
        """Obtiene importancia de cada característica."""
        try:
            if self.model is None or not self.is_trained:
                return {}
            
            importances = self.model.feature_importances_
            
            return {
                name: float(importance) 
                for name, importance in zip(self.feature_names, importances)
            }
            
        except Exception as e:
            log_error(f"Error obteniendo importancia: {e}")
            return {}
