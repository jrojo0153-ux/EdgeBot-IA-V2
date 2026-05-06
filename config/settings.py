"""Configuración centralizada de EdgeBot-IA-V2 con soporte ML"""
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Optional

# 🔥 Zona horaria de México (UTC-6)
MX_TZ = timezone(timedelta(hours=-6))
HOY_ESPN = datetime.now(MX_TZ).strftime("%Y%m%d")

class Settings:
    """Configuración global del bot."""
    
    # API Keys (Variables de entorno)
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")
    
    # URLs de APIs
    GROQ_API_URL: str = "https://api.groq.com/openai/v1/chat/completions"
    TELEGRAM_API_URL: str = ""
    
    # URLs ESPN dinámicas
    ESPN_URLS: dict = {
        "nba": f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={HOY_ESPN}",
        "mlb": f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates={HOY_ESPN}",
        "mex_soccer": f"https://site.api.espn.com/apis/site/v2/sports/soccer/mex.1/scoreboard?dates={HOY_ESPN}",
        "eng_soccer": f"https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard?dates={HOY_ESPN}",
        "esp_soccer": f"https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard?dates={HOY_ESPN}",
        "ita_soccer": f"https://site.api.espn.com/apis/site/v2/sports/soccer/ita.1/scoreboard?dates={HOY_ESPN}",
        "ger_soccer": f"https://site.api.espn.com/apis/site/v2/sports/soccer/ger.1/scoreboard?dates={HOY_ESPN}",
        "fra_soccer": f"https://site.api.espn.com/apis/site/v2/sports/soccer/fra.1/scoreboard?dates={HOY_ESPN}"
    }
    
    # Parámetros del bot
    MAX_PICKS_PER_RUN: int = 5
    REQUEST_TIMEOUT: int = 15
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_TEMPERATURE: float = 0.2
    DELAY_BETWEEN_PICKS: int = 3
    
    # Rate Limiting
    ESPN_RATE_LIMIT: int = 10
    GROQ_RATE_LIMIT: int = 30
    
    # 🆕 Parámetros de Machine Learning
    ML_MODEL_PATH: str = os.path.join("models", "edgebot_model.pkl")
    ML_TRAINING_DATA_PATH: str = os.path.join("data", "training_data.csv")
    ML_MIN_SAMPLES_FOR_TRAINING: int = 50  # Mínimo de muestras para entrenar
    ML_RETRAIN_THRESHOLD: int = 10  # Retrenar cada X nuevas muestras
    ML_CONFIDENCE_THRESHOLD: float = 0.65  # Confianza mínima para aprobar pick
    
    # Rutas de datos
    DATA_DIR: str = "data"
    LOGS_DIR: str = "logs"
    MODELS_DIR: str = "models"
    
    # Archivos
    FILES: dict = {
        "aprendizaje": os.path.join(DATA_DIR, "aprendizaje.txt"),
        "historial": os.path.join(DATA_DIR, "historial_resultados.txt"),
        "procesados": os.path.join(DATA_DIR, "procesados.txt"),
        "predicciones_pendientes": os.path.join(DATA_DIR, "predicciones_pendientes.json"),
        "metricas": os.path.join(DATA_DIR, "metricas.json"),
        "training_data": ML_TRAINING_DATA_PATH
    }
    
    # Base de datos SQLite
    DB_PATH: str = os.path.join(DATA_DIR, "edgebot.db")
    
    @staticmethod
    def crear_directorios():
        """Crea los directorios necesarios."""
        os.makedirs(Settings.DATA_DIR, exist_ok=True)
        os.makedirs(Settings.LOGS_DIR, exist_ok=True)
        os.makedirs(Settings.MODELS_DIR, exist_ok=True)
    
    @staticmethod
    def validar_configuracion() -> bool:
        """Valida configuraciones requeridas."""
        from utils.logger import log_error, log_info
        
        errores = []
        
        if not Settings.GROQ_API_KEY:
            errores.append("❌ GROQ_API_KEY no configurada")
        if not Settings.TELEGRAM_BOT_TOKEN:
            errores.append("❌ TELEGRAM_BOT_TOKEN no configurada")
        if not Settings.TELEGRAM_CHAT_ID:
            errores.append("❌ TELEGRAM_CHAT_ID no configurada")
        
        if errores:
            log_error("=" * 50)
            log_error("ERROR DE CONFIGURACIÓN CRÍTICA")
            log_error("=" * 50)
            for error in errores:
                log_error(error)
            log_error("=" * 50)
            return False
        
        Settings.TELEGRAM_API_URL = f"https://api.telegram.org/bot{Settings.TELEGRAM_BOT_TOKEN}"
        log_info("✅ Configuración validada exitosamente")
        return True
    
    @staticmethod
    def inicializar():
        """Inicializa todas las configuraciones."""
        Settings.crear_directorios()
        return Settings.validar_configuracion()
