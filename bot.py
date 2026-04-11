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
    partidos = []
    
    urls =[
        "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
        "https://site.api.espn.com/apis/site/v2/sports/soccer/mex.1/scoreboard",
        "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard",
        "https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.champions/scoreboard"
    ]
    
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if "events" in data:
                for evento in data["events"]:
                    nombre = evento["name"]
                    estado = evento["status"]["type"]["state"]
                    
                    if estado == "pre":
                        partidos.append(nombre)
        except Exception as e:
            print(f"Error al consultar ESPN: {e}")
            
    return partidos[:5]

def analizar_con_ia(historial, partido):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    
    # PROMPT CORREGIDO: AHORA EXIGE EL PICK SUGERIDO
    prompt = f"""[ROL Y OBJETIVO]
    Eres un Analista Cuantitativo (EDGE BOT PRO).
    Tu obligación ESTRICTA es escanear TODAS las reglas de este historial y aplicar TODAS las que coincidan con el contexto del partido:
    {historial}
    
    Analiza este partido: {partido}
    
    [FORMATO DE SALIDA ESTRICTO]
    PROHIBIDO escribir párrafos.
    Responde EXACTAMENTE con esta estructura de 6 líneas:

    🔍 REGLAS ACTIVADAS: [Nombra los corchetes de las reglas del historial que usaste]
    🧠 ANÁLISIS:[1 sola oración técnica explicando cómo interactúan esas reglas en este partido]
    📌 PICK SUGERIDO:[Dime EXACTAMENTE a qué apostar. Ej: Local Gana, Visitante +0.5, Under 2.5 goles]
    🎯 PROBABILIDAD: [X%]
    📈 EDGE / VALOR: [+Y%]
    ⚖️ VEREDICTO: [APROBADO o DESCARTADO]
    """
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages":[
            {"role": "system", "content": "Eres un bot matemático. Eres frío, directo y escaneas bases de datos de reglas antes de responder."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    
    try:
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
        response = requests.post(url, json=payload, timeout=10)
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
        enviar_telegram("⚠️ EDGE BOT PRO\nNo hay partidos programados hoy en las ligas principales.")
        return
        
    for partido in partidos:
        analisis = analizar_con_ia(historial, partido)
        
        mensaje_final = f"""🤖 𝗘𝗗𝗚𝗘 𝗕𝗢𝗧 𝗣𝗥𝗢
━━━━━━━━━━━━━━━━━━━━
⚽ 𝗣𝗔𝗥𝗧𝗜𝗗𝗢:
{partido}

{analisis}
━━━━━━━━━━━━━━━━━━━━"""
        
        enviar_telegram(mensaje_final)
        time.sleep(3)
        
    print("Proceso finalizado.")

if __name__ == "__main__":
    main()
