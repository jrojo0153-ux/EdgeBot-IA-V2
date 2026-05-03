"""Clientes de APIs para EdgeBot-IA-V2"""
import requests
import json
from config.settings import Settings
from .logger import log_info, log_error, log_debug


class ESPNClient:
    """Cliente para obtener datos de ESPN."""
    
    @staticmethod
    def obtener_partidos_por_jugar():
        """Obtiene partidos próximos a jugarse (estado: pre)."""
        partidos = []
        
        for liga_key, url in Settings.ESPN_URLS.items():
            try:
                response = requests.get(url, timeout=Settings.REQUEST_TIMEOUT)
                data = response.json()
                
                if "events" in data:
                    for evento in data["events"]:
                        if evento["status"]["type"]["state"] == "pre":
                            try:
                                competitors = evento["competitions"][0]["competitors"]
                                home = next(c["team"]["name"] for c in competitors if c["homeAway"] == "home")
                                away = next(c["team"]["name"] for c in competitors if c["homeAway"] == "away")
                                liga = data["leagues"][0]["name"]
                                
                                partido_str = f"[{liga}] LOCAL: {home} vs VISITANTE: {away}"
                                partidos.append((liga_key, home, away, partido_str, liga))
                            except:
                                pass
            except Exception as e:
                log_debug(f"Error al consultar {liga_key} en ESPN: {e}")
        
        return partidos
    
    @staticmethod
    def obtener_resultados_finalizados():
        """Obtiene partidos finalizados (estado: post)."""
        resultados = []
        
        for liga_key, url in Settings.ESPN_URLS.items():
            try:
                response = requests.get(url, timeout=Settings.REQUEST_TIMEOUT)
                data = response.json()
                
                if "events" in data:
                    for evento in data["events"]:
                        if evento["status"]["type"]["state"] == "post":
                            try:
                                competitors = evento["competitions"][0]["competitors"]
                                home = next(c["team"]["name"] for c in competitors if c["homeAway"] == "home")
                                away = next(c["team"]["name"] for c in competitors if c["homeAway"] == "away")
                                home_score = next(c["score"] for c in competitors if c["homeAway"] == "home")
                                away_score = next(c["score"] for c in competitors if c["homeAway"] == "away")
                                
                                marcador = f"{home} {home_score} - {away_score} {away}"
                                resultados.append((home, away, marcador))
                            except:
                                pass
            except Exception as e:
                log_debug(f"Error al consultar resultados en {liga_key}: {e}")
        
        return resultados


class GroqClient:
    """Cliente para análisis con Groq AI."""
    
    @staticmethod
    def analizar_partido(historial, partido_str):
        """Analiza un partido usando IA de Groq."""
        url = Settings.GROQ_API_URL
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {Settings.GROQ_API_KEY}"
        }
        
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
            response = requests.post(url, headers=headers, json=payload, timeout=Settings.REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                log_error(f"Error Groq ({response.status_code}): {response.text}")
                return None
        except Exception as e:
            log_error(f"Error de conexión con Groq: {e}")
            return None
    
    @staticmethod
    def auditar_resultado(partido_str, analisis_previo, marcador_real):
        """Audita un resultado y genera nuevas reglas."""
        url = Settings.GROQ_API_URL
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {Settings.GROQ_API_KEY}"
        }
        
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
            response = requests.post(url, headers=headers, json=payload, timeout=Settings.REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                log_error(f"Error Groq en auditoría ({response.status_code}): {response.text}")
                return None
        except Exception as e:
            log_error(f"Error de conexión con Groq (auditoría): {e}")
            return None


class TelegramClient:
    """Cliente para envío de mensajes por Telegram."""
    
    @staticmethod
    def enviar_mensaje(mensaje):
        """Envía un mensaje a Telegram."""
        if not Settings.TELEGRAM_BOT_TOKEN or not Settings.TELEGRAM_CHAT_ID:
            log_error("Variables de Telegram no configuradas")
            return False
        
        url = f"{Settings.TELEGRAM_API_URL}/sendMessage"
        payload = {
            "chat_id": Settings.TELEGRAM_CHAT_ID,
            "text": mensaje
        }
        
        try:
            response = requests.post(url, json=payload, timeout=Settings.REQUEST_TIMEOUT)
            if response.status_code == 200:
                log_debug("Mensaje enviado a Telegram")
                return True
            else:
                log_error(f"Error al enviar a Telegram ({response.status_code}): {response.text}")
                return False
        except Exception as e:
            log_error(f"Error de conexión Telegram: {e}")
            return False
