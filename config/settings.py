"""Configuración centralizada de EdgeBot-IA-V2"""
import os
from datetime import datetime


class Settings:
    """Configuración global del bot."""
    
    # API Keys (Variables de entorno)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # URLs de APIs
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    
    ESPN_URLS = {
        "nba": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
        "mlb": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
        "mex_soccer": "https://site.api.espn.com/apis/site/v2/sports/soccer/mex.1/scoreboard",
        "eng_soccer": "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard",
        "esp_soccer": "https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard",
        "ita_soccer": "https://site.api.espn.com/apis/site/v2/sports/soccer/ita.1/scoreboard",
        "ger_soccer": "https://site.api.espn.com/apis/site/v2/sports/soccer/ger.1/scoreboard",
        "fra_soccer": "https://site.api.espn.com/apis/site/v2/sports/soccer/fra.1/scoreboard"
    }
    
    # Parámetros del bot
    MAX_PICKS_PER_RUN = 5
    REQUEST_TIMEOUT = 15
    GROQ_MODEL = "llama-3.3-70b-versatile"
    GROQ_TEMPERATURE = 0.2
    DELAY_BETWEEN_PICKS = 3  # segundos
    
    # Rutas de datos
    DATA_DIR = "data"
    LOGS_DIR = "logs"
    
    FILES = {
        "aprendizaje": os.path.join(DATA_DIR, "aprendizaje.txt"),
        "historial": os.path.join(DATA_DIR, "historial_resultados.txt"),
        "procesados": os.path.join(DATA_DIR, "procesados.txt"),
        "predicciones_pendientes": os.path.join(DATA_DIR, "predicciones_pendientes.json")
    }
    
    @staticmethod
    def crear_directorios():
        """Crea los directorios necesarios si no existen."""
        os.makedirs(Settings.DATA_DIR, exist_ok=True)
        os.makedirs(Settings.LOGS_DIR, exist_ok=True)
