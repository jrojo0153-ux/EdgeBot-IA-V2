import os
import json
import requests
from datetime import datetime

# ==========================================
# CONFIGURACIÓN DE VARIABLES DE ENTORNO
# (Debes configurar estos Secrets en GitHub)
# ==========================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def leer_aprendizaje():
    """Lee el archivo de texto con el historial de fallos/aciertos."""
    ruta = "data/aprendizaje.txt"
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as file:
            return file.read()
    return "No hay datos históricos previos. Inicia con análisis base."

def obtener_partidos_hoy():
    """Obtiene partidos del día desde TheSportsDB (Tier Gratuito)."""
    hoy = datetime.today().strftime('%Y-%m-%d')
    # Endpoint gratuito para eventos del día (Fútbol)
    url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={hoy}&s=Soccer"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        partidos =[]
        
        if data.get("events"):
            # Tomamos solo los primeros 3 partidos para no saturar la API de OpenAI
            for evento in data["events"][:3]:
                partido = f"{evento['strEvent']} ({evento['strLeague']})"
                partidos.append(partido)
        return partidos
    except Exception as e:
        print(f"Error al obtener partidos: {e}")
        return[]

def analizar_con_ia(historial, partido):
    """Envía el historial y el partido a GPT-4o-mini vía API REST directa."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    prompt = f"""[ROL Y OBJETIVO]
    Eres un Sistema de Análisis Predictivo Evolutivo (EDGE BOT PRO).
    Aprende obligatoriamente de este historial de fallos y aciertos antes de predecir:[HISTORIAL RECIENTE PARA APRENDIZAJE]
    {historial}
    
    [NUEVO EVENTO A PREDECIR]
    Analiza el siguiente partido: {partido}
    
    [FORMATO DE SALIDA ESTRICTO]
    - Reflexión Breve: (Qué aprendiste del historial que aplicas aquí)
    - Probabilidad Calculada: X%
    - Edge / Valor: Y%
    - Veredicto Final:[APROBADO / DESCARTADO]
    """
    
    payload = {
        "model": "gpt-4o-mini",
        "messages":[
            {"role": "system", "content": "Eres un Analista Cuantitativo de Deportes."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"Error OpenAI: {response.text}"
    except Exception as e:
        return f"Error de conexión con OpenAI: {e}"

def enviar_telegram(mensaje):
    """Envía el resultado final a tu chat de Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error al enviar a Telegram: {e}")

def main():
    print("Iniciando Edge Bot Pro...")
    
    # 1. Leer aprendizaje
    historial = leer_aprendizaje()
    
    # 2. Obtener partidos
    partidos = obtener_partidos_hoy()
    
    if not partidos:
        enviar_telegram("⚠️ *EDGE BOT PRO*\nNo se encontraron partidos de fútbol para hoy en TheSportsDB.")
        return
        
    # 3. Analizar y enviar
    for partido in partidos:
        print(f"Analizando: {partido}")
        analisis = analizar_con_ia(historial, partido)
        
        mensaje_final = f"🤖 *EDGE BOT PRO - PREDICCIÓN*\n\n⚽ *Partido:* {partido}\n\n{analisis}"
        enviar_telegram(mensaje_final)
        
    print("Proceso finalizado con éxito.")

if __name__ == "__main__":
    main()
