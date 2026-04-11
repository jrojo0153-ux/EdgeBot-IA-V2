import os
import requests
import time
from datetime import datetime

# ==========================================
# CONFIGURACIÓN DE VARIABLES DE ENTORNO
# ==========================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def leer_aprendizaje():
    ruta = "data/aprendizaje.txt"
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as file:
            return file.read()
    return "No hay datos históricos previos."

def obtener_partidos_hoy():
    print("Buscando partidos reales en la API de ESPN...")
    partidos =[]
    
    # Endpoints públicos de ESPN (100% gratuitos, sin API Key y en tiempo real)
    urls =[
        "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",       # NBA
        "https://site.api.espn.com/apis/site/v2/sports/soccer/mex.1/scoreboard",         # Liga MX
        "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard",         # Premier League
        "https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.champions/scoreboard" # Champions League
    ]
    
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if "events" in data:
                for evento in data["events"]:
                    nombre = evento["name"]
                    estado = evento["status"]["type"]["state"]
                    
                    # Solo tomar partidos que NO han comenzado ("pre")
                    if estado == "pre":
                        partidos.append(nombre)
        except Exception as e:
            print(f"Error al consultar ESPN: {e}")
            
    print(f"Partidos encontrados hoy: {partidos}")
    
    # Devolver solo los primeros 5 para no saturar el bot ni tu Telegram
    return partidos[:5]

def analizar_con_ia(historial, partido):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    
    prompt = f"""[ROL Y OBJETIVO]
    Eres un Sistema de Análisis Predictivo Evolutivo (EDGE BOT PRO).
    Aprende obligatoriamente de este historial de reglas matemáticas:
    {historial}
    
    Analiza el siguiente partido programado para hoy: {partido}
    
    [FORMATO DE SALIDA ESTRICTO]
    - Reflexión Breve: (Aplica una regla del historial si encaja)
    - Probabilidad Calculada: X%
    - Edge / Valor: Y%
    - Veredicto Final: [APROBADO / DESCARTADO]
    """
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages":[
            {"role": "system", "content": "Eres un Analista Cuantitativo de Deportes. Eres directo, matemático y no das respuestas genéricas."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6
    }
    
    try:
        print(f"Enviando {partido} a Groq...")
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"Error Groq: {response.text}"
    except Exception as e:
        return f"Error de conexión con Groq: {e}"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje
    }
    try:
        print("Intentando enviar mensaje a Telegram...")
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"❌ ERROR DE TELEGRAM: {response.text}")
        else:
            print("✅ Mensaje enviado a Telegram con éxito.")
    except Exception as e:
        print(f"❌ Excepción al enviar a Telegram: {e}")

def main():
    print("Iniciando Edge Bot Pro (Conectado a ESPN)...")
    
    historial = leer_aprendizaje()
    partidos = obtener_partidos_hoy()
    
    if not partidos:
        enviar_telegram("⚠️ EDGE BOT PRO\nNo se encontraron partidos de NBA, Liga MX o Premier League programados para hoy.")
        return
        
    for partido in partidos:
        analisis = analizar_con_ia(historial, partido)
        mensaje_final = f"🤖 EDGE BOT PRO\n\n⚽ Partido: {partido}\n\n{analisis}"
        enviar_telegram(mensaje_final)
        
        # Pausa de 3 segundos para no saturar la API gratuita de Groq
        print("Pausando 3 segundos para evitar Rate Limit...")
        time.sleep(3)
        
    print("Proceso finalizado.")

if __name__ == "__main__":
    main()
