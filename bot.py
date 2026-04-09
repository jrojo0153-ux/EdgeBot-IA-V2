import os
import json
import requests
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
    hoy = datetime.today().strftime('%Y-%m-%d')
    url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={hoy}&s=Soccer"
    print(f"Buscando partidos para la fecha: {hoy}")
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        partidos = []
        
        if data.get("events"):
            for evento in data["events"][:3]:
                partido = f"{evento['strEvent']} ({evento['strLeague']})"
                partidos.append(partido)
            print(f"Partidos encontrados: {partidos}")
        else:
            print("La API no devolvió partidos para hoy.")
            
        return partidos
    except Exception as e:
        print(f"Error al obtener partidos: {e}")
        return[]

def analizar_con_ia(historial, partido):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    
    prompt = f"""[ROL Y OBJETIVO]
    Eres un Sistema de Análisis Predictivo Evolutivo (EDGE BOT PRO).
    Aprende de este historial:
    {historial}
    
    Analiza el siguiente partido: {partido}
    
    [FORMATO DE SALIDA ESTRICTO]
    - Reflexión Breve:
    - Probabilidad Calculada: X%
    - Edge / Valor: Y%
    - Veredicto Final: [APROBADO / DESCARTADO]
    """
    
    payload = {
        "model": "llama3-70b-8192",
        "messages":[
            {"role": "system", "content": "Eres un Analista Cuantitativo de Deportes."},
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
            print(f"Error Groq: {response.text}")
            return f"Error Groq: {response.text}"
    except Exception as e:
        print(f"Excepción con Groq: {e}")
        return f"Error de conexión con Groq: {e}"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    try:
        print("Intentando enviar mensaje a Telegram...")
        response = requests.post(url, json=payload, timeout=10)
        # ESTO ES CLAVE: Imprimir la respuesta de Telegram
        if response.status_code != 200:
            print(f"❌ ERROR DE TELEGRAM: {response.text}")
        else:
            print("✅ Mensaje enviado a Telegram con éxito.")
    except Exception as e:
        print(f"❌ Excepción al enviar a Telegram: {e}")

def main():
    print("Iniciando Edge Bot Pro...")
    
    historial = leer_aprendizaje()
    partidos = obtener_partidos_hoy()
    
    if not partidos:
        enviar_telegram("⚠️ *EDGE BOT PRO*\nNo se encontraron partidos de fútbol para hoy en TheSportsDB.")
        return
        
    for partido in partidos:
        analisis = analizar_con_ia(historial, partido)
        mensaje_final = f"🤖 *EDGE BOT PRO*\n\n⚽ *Partido:* {partido}\n\n{analisis}"
        enviar_telegram(mensaje_final)
        
    print("Proceso finalizado.")

if __name__ == "__main__":
    main()
