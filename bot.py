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
                    estado = evento["status"]["type"]["state"]
                    
                    if estado == "pre":
                        # ====================================================
                        # EXTRACCIÓN EXACTA DE LOCAL Y VISITANTE DESDE EL JSON
                        # ====================================================
                        try:
                            competitors = evento["competitions"][0]["competitors"]
                            home_team = next(c["team"]["name"] for c in competitors if c["homeAway"] == "home")
                            away_team = next(c["team"]["name"] for c in competitors if c["homeAway"] == "away")
                            liga = data["leagues"][0]["name"]
                            
                            # Formato a prueba de errores para la IA
                            partido_str = f"[{liga}] LOCAL: {home_team} vs VISITANTE: {away_team}"
                        except:
                            # Fallback por si el JSON cambia
                            partido_str = evento["name"]
                            
                        partidos.append(partido_str)
        except Exception as e:
            print(f"Error al consultar ESPN: {e}")
            
    return partidos[:5]

def analizar_con_ia(historial, partido):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    
    # PROMPT BLINDADO CONTRA ERRORES DE LOCALÍA
    prompt = f"""[ROL Y OBJETIVO]
    Eres un Analista Cuantitativo (EDGE BOT PRO).
    Tu obligación es leer el partido, identificar EXACTAMENTE quién es el LOCAL y quién el VISITANTE, y aplicar las reglas de este historial:
    {historial}
    
    Analiza este partido: {partido}
    
    [REGLA VITAL]
    El texto te dice explícitamente quién es LOCAL y quién es VISITANTE. NO LOS CONFUNDAS. Aplica las reglas de localía/visita correctamente.
    
    [FORMATO DE SALIDA ESTRICTO]
    PROHIBIDO escribir párrafos.
    Responde EXACTAMENTE con esta estructura de 6 líneas:

    🔍 REGLAS ACTIVADAS: [Nombra los corchetes de las reglas del historial que usaste]
    🧠 ANÁLISIS:[1 sola oración técnica explicando por qué el Pick tiene valor basándote en quién es el local y el visitante]
    📌 PICK SUGERIDO:[Dime EXACTAMENTE a qué apostar. Ej: Gana Local, Gana Visitante, Empate, Under de goles]
    🎯 PROBABILIDAD:[X%]
    📈 EDGE / VALOR: [+Y%]
    ⚖️ VEREDICTO:[APROBADO o DESCARTADO]
    """
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages":[
            {"role": "system", "content": "Eres un bot matemático. Eres frío, directo, NUNCA confundes local con visitante y escaneas bases de datos de reglas antes de responder."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1 # Temperatura casi en cero para máxima precisión lógica
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
