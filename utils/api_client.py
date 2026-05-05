"""Clientes de APIs para EdgeBot-IA-V2 con mejoras de performance y seguridad"""
import requests
import json
import time
import re
import html
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, List, Tuple, Dict, Any
from config.settings import Settings
from .logger import log_info, log_error, log_debug


# ============================================================================
# DECORADORES Y UTILIDADES
# ============================================================================

def retry_on_failure(max_attempts: int = 3, base_delay: int = 1):
    """Decorator para reintentos con exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        log_error(f"Fallo después de {max_attempts} intentos: {e}")
                        raise
                    delay = base_delay * (2 ** attempt)
                    log_info(f"Reintentando en {delay}s (intento {attempt + 1}/{max_attempts})")
                    time.sleep(delay)
        return wrapper
    return decorator


class RateLimiter:
    """Controla límites de tasa para APIs."""
    
    def __init__(self, max_calls: int, period_seconds: int):
        self.max_calls: int = max_calls
        self.period: timedelta = timedelta(seconds=period_seconds)
        self.calls: List[datetime] = []
    
    def wait_if_needed(self):
        """Espera si se excede el límite de tasa."""
        now = datetime.now()
        self.calls = [call for call in self.calls if now - call < self.period]
        
        if len(self.calls) >= self.max_calls:
            oldest = self.calls[0]
            sleep_time = (self.period - (now - oldest)).total_seconds()
            if sleep_time > 0:
                log_info(f"Rate limit: esperando {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        self.calls.append(datetime.now())


class APICache:
    """Cache simple para respuestas de API."""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache: Dict[str, Tuple[dict, float]] = {}
        self.ttl: int = ttl_seconds
    
    def _generate_key(self, url: str, params: Optional[dict] = None) -> str:
        """Genera clave única para cache."""
        key_str = f"{url}:{json.dumps(params or {}, sort_keys=True)}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, url: str, params: Optional[dict] = None) -> Optional[dict]:
        """Obtiene del cache si existe y no expiró."""
        key = self._generate_key(url, params)
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now().timestamp() - timestamp < self.ttl:
                return data
            del self.cache[key]
        return None
    
    def set(self, url: str, data: dict, params: Optional[dict] = None):
        """Guarda en cache."""
        key = self._generate_key(url, params)
        self.cache[key] = (data, datetime.now().timestamp())


def sanitize_string(value: Any) -> str:
    """Sanitiza strings de APIs externas."""
    if not isinstance(value, str):
        return str(value) if value is not None else ""
    # Decodificar HTML entities
    value = html.unescape(value)
    # Remover caracteres peligrosos
    value = re.sub(r'[<>\"\'&]', '', value)
    return value.strip()[:200]  # Limitar longitud


# ============================================================================
# CLIENTES DE API
# ============================================================================

# Instancias globales de rate limiting y cache
espn_limiter = RateLimiter(max_calls=Settings.ESPN_RATE_LIMIT, period_seconds=60)
groq_limiter = RateLimiter(max_calls=Settings.GROQ_RATE_LIMIT, period_seconds=60)
espn_cache = APICache(ttl_seconds=300)  # 5 minutos


class ESPNClient:
    """Cliente para obtener datos de ESPN con rate limiting y cache."""
    
    @staticmethod
    @retry_on_failure(max_attempts=3)
    def obtener_partidos_por_jugar() -> List[Tuple[str, str, str, str, str]]:
        """Obtiene partidos próximos a jugarse (estado: pre)."""
        partidos: List[Tuple[str, str, str, str, str]] = []
        
        for liga_key, url in Settings.ESPN_URLS.items():
            try:
                # Rate limiting
                espn_limiter.wait_if_needed()
                
                # Check cache
                cached = espn_cache.get(url)
                if cached:
                    log_debug(f"Cache hit para {liga_key}")
                    data = cached
                else:
                    response = requests.get(url, timeout=Settings.REQUEST_TIMEOUT)
                    response.raise_for_status()
                    data = response.json()
                    espn_cache.set(url, data)
                
                if "events" in data:
                    for evento in data["events"]:
                        if evento["status"]["type"]["state"] == "pre":
                            try:
                                competitors = evento["competitions"][0]["competitors"]
                                home = sanitize_string(next(c["team"]["name"] for c in competitors if c["homeAway"] == "home"))
                                away = sanitize_string(next(c["team"]["name"] for c in competitors if c["homeAway"] == "away"))
                                liga = sanitize_string(data["leagues"][0]["name"])
                                
                                partido_str = f"[{liga}] LOCAL: {home} vs VISITANTE: {away}"
                                partidos.append((liga_key, home, away, partido_str, liga))
                            except Exception as e:
                                log_debug(f"Error procesando evento en {liga_key}: {e}")
            except Exception as e:
                log_error(f"Error al consultar {liga_key} en ESPN: {e}")
        
        log_info(f"ESPN: {len(partidos)} partidos encontrados")
        return partidos
    
    @staticmethod
    @retry_on_failure(max_attempts=3)
    def obtener_resultados_finalizados() -> List[Tuple[str, str, str]]:
        """Obtiene partidos finalizados (estado: post)."""
        resultados: List[Tuple[str, str, str]] = []
        
        for liga_key, url in Settings.ESPN_URLS.items():
            try:
                # Rate limiting
                espn_limiter.wait_if_needed()
                
                response = requests.get(url, timeout=Settings.REQUEST_TIMEOUT)
                response.raise_for_status()
                data = response.json()
                
                if "events" in data:
                    for evento in data["events"]:
                        if evento["status"]["type"]["state"] == "post":
                            try:
                                competitors = evento["competitions"][0]["competitors"]
                                home = sanitize_string(next(c["team"]["name"] for c in competitors if c["homeAway"] == "home"))
                                away = sanitize_string(next(c["team"]["name"] for c in competitors if c["homeAway"] == "away"))
                                home_score = sanitize_string(next(c["score"] for c in competitors if c["homeAway"] == "home"))
                                away_score = sanitize_string(next(c["score"] for c in competitors if c["homeAway"] == "away"))
                                
                                marcador = f"{home} {home_score} - {away_score} {away}"
                                resultados.append((home, away, marcador))
                            except Exception as e:
                                log_debug(f"Error procesando resultado en {liga_key}: {e}")
            except Exception as e:
                log_error(f"Error al consultar resultados en {liga_key}: {e}")
        
        log_info(f"ESPN: {len(resultados)} resultados finalizados encontrados")
        return resultados


class GroqClient:
    """Cliente para análisis con Groq AI con validación de input."""
    
    @staticmethod
    def _validar_respuesta_analisis(respuesta: str) -> bool:
        """Valida que la respuesta de IA tenga el formato esperado."""
        if not respuesta:
            return False
        
        patrones_requeridos = [
            r"🔍 REGLAS ACTIVADAS:",
            r"🧠 ANÁLISIS:",
            r"📌 PICK SUGERIDO:",
            r"🎯 PROBABILIDAD REAL:",
            r"💰 CUOTA MÍNIMA",
            r"⚖️ VEREDICTO:"
        ]
        
        for patron in patrones_requeridos:
            if not re.search(patron, respuesta, re.IGNORECASE):
                log_error(f"Respuesta IA no contiene: {patron}")
                return False
        return True
    
    @staticmethod
    def _validar_respuesta_auditoria(respuesta: str) -> bool:
        """Valida que la respuesta de auditoría tenga el formato esperado."""
        if not respuesta:
            return False
        
        patrones_requeridos = [
            r"RESULTADO:",
            r"LECCIÓN:",
            r"REGLA:"
        ]
        
        for patron in patrones_requeridos:
            if not re.search(patron, respuesta, re.IGNORECASE):
                log_error(f"Auditoría IA no contiene: {patron}")
                return False
        return True
    
    @staticmethod
    @retry_on_failure(max_attempts=3)
    def analizar_partido(historial: str, partido_str: str) -> Optional[str]:
        """Analiza un partido usando IA de Groq."""
        url = Settings.GROQ_API_URL
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {Settings.GROQ_API_KEY}"
        }
        
        # Sanitizar input
        partido_str = sanitize_string(partido_str)
        historial = sanitize_string(historial)[:5000]  # Limitar historial
        
        prompt = f"""[ROL Y OBJETIVO]
Eres un Analista Cuantitativo (EDGE BOT PRO).
Lee este historial de reglas:
{historial}

Analiza este partido: {partido_str}

[REGLAS VITALES DE CÁLCULO]
1. NO INVENTES EL EDGE.
2. Calcula la PROBABILIDAD REAL (X%).
3. Calcula la CUOTA MÍNIMA RENTABLE dividiendo 100 entre tu Probabilidad.
4. Si no hay valor claro, tu Veredicto DEBE ser DESCARTADO. Sé muy estricto.

[FORMATO DE SALIDA ESTRICTO]
PROHIBIDO escribir párrafos.
Responde EXACTAMENTE con esta estructura de 6 líneas:

🔍 REGLAS ACTIVADAS: [Nombra las reglas del historial que usaste]
🧠 ANÁLISIS: [1 sola oración técnica explicando el pick]
📌 PICK SUGERIDO: [Dime EXACTAMENTE a qué apostar]
🎯 PROBABILIDAD REAL: [X%]
💰 CUOTA MÍNIMA (+EV): [Calcula: 100 / X]
⚖️ VEREDICTO: [APROBADO o DESCARTADO]
"""
        
        payload = {
            "model": Settings.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "Eres un bot matemático. Eres frío, directo y descartas apuestas si no hay valor matemático claro."},
                {"role": "user", "content": prompt}
            ],
            "temperature": Settings.GROQ_TEMPERATURE
        }
        
        try:
            # Rate limiting
            groq_limiter.wait_if_needed()
            
            response = requests.post(url, headers=headers, json=payload, timeout=Settings.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            contenido = response.json()["choices"][0]["message"]["content"]
            
            # Validar respuesta
            if GroqClient._validar_respuesta_analisis(contenido):
                log_info("✅ Respuesta de IA validada correctamente")
                return contenido
            else:
                log_error("❌ Respuesta de IA no válida, descartando")
                return None
                
        except requests.exceptions.HTTPError as e:
            log_error(f"Error HTTP Groq ({response.status_code}): {e}")
            return None
        except Exception as e:
            log_error(f"Error de conexión con Groq: {e}")
            return None
    
    @staticmethod
    @retry_on_failure(max_attempts=3)
    def auditar_resultado(partido_str: str, analisis_previo: str, marcador_real: str) -> Optional[str]:
        """Audita un resultado y genera nuevas reglas."""
        url = Settings.GROQ_API_URL
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {Settings.GROQ_API_KEY}"
        }
        
        # Sanitizar inputs
        partido_str = sanitize_string(partido_str)
        analisis_previo = sanitize_string(analisis_previo)[:2000]
        marcador_real = sanitize_string(marcador_real)
        
        prompt = f"""[AUDITORÍA DE MODELO CUANTITATIVO]
Partido: {partido_str}
Marcador Real Final: {marcador_real}
Predicción que hizo el bot: {analisis_previo}

Evalúa si la apuesta fue GANADA o PERDIDA según el marcador real.
Extrae una lección cuantitativa y genera una regla de 1 línea para el futuro.

FORMATO ESTRICTO:
RESULTADO: [GANADA o PERDIDA]
LECCIÓN: [Breve análisis de la varianza o error]
REGLA: [Instrucción matemática corta para el bot]
"""
        
        payload = {
            "model": Settings.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "Eres un auditor de datos. Analizas victorias y derrotas de modelos predictivos deportivos."},
                {"role": "user", "content": prompt}
            ],
            "temperature": Settings.GROQ_TEMPERATURE
        }
        
        try:
            # Rate limiting
            groq_limiter.wait_if_needed()
            
            response = requests.post(url, headers=headers, json=payload, timeout=Settings.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            contenido = response.json()["choices"][0]["message"]["content"]
            
            # Validar respuesta
            if GroqClient._validar_respuesta_auditoria(contenido):
                log_info("✅ Auditoría de IA validada correctamente")
                return contenido
            else:
                log_error("❌ Auditoría de IA no válida, descartando")
                return None
                
        except requests.exceptions.HTTPError as e:
            log_error(f"Error HTTP Groq en auditoría ({response.status_code}): {e}")
            return None
        except Exception as e:
            log_error(f"Error de conexión con Groq (auditoría): {e}")
            return None


class TelegramClient:
    """Cliente para envío de mensajes por Telegram."""
    
    @staticmethod
    @retry_on_failure(max_attempts=2)
    def enviar_mensaje(mensaje: str) -> bool:
        """Envía un mensaje a Telegram."""
        if not Settings.TELEGRAM_BOT_TOKEN or not Settings.TELEGRAM_CHAT_ID:
            log_error("Variables de Telegram no configuradas")
            return False
        
        # Sanitizar mensaje
        mensaje = sanitize_string(mensaje)[:4000]  # Límite de Telegram
        
        url = f"{Settings.TELEGRAM_API_URL}/sendMessage"
        payload = {
            "chat_id": Settings.TELEGRAM_CHAT_ID,
            "text": mensaje,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=Settings.REQUEST_TIMEOUT)
            response.raise_for_status()
            log_debug("Mensaje enviado a Telegram")
            return True
        except requests.exceptions.HTTPError as e:
            log_error(f"Error HTTP Telegram ({response.status_code}): {e}")
            return False
        except Exception as e:
            log_error(f"Error de conexión Telegram: {e}")
            return False
