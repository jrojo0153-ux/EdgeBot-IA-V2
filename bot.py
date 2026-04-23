import os
import requests
import time
import json
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

def cargar_procesados():
    ruta = "data/procesados.txt"
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as file:
            return file.read().splitlines()
    return []

def guardar_procesado(partido_id):
    os.makedirs("data", exist_ok=True)
    with open("data/procesados.txt", "a", encoding="utf-8") as file:
        file.write(partido_id + "\n")

# NUEVA FUNCIÓN: Guarda el pick aprobado para que aprendizaje.py lo evalúe después
def guardar_prediccion_pendiente(partido_id, partido_str, analisis):
    os.makedirs("data", exist_ok=True)
    ruta = "data/predicciones_pendientes.json"
    pendientes = {}
    
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                pendientes = json.load(f)
        except:
            pass
            
    pendientes[partido_id] = {
        "partido_str": partido_str,
        "analisis": analisis,
        "fecha": datetime.today().strftime('%Y-%m-%d')
    }
    
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(pendientes, f, ensure_ascii=False, indent=4)

def obtener_partidos_hoy():
    print("Buscando partidos en las 8 ligas top (ESPN API)...")
    partidos = []
    
    urls = [
        "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
        "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
        "https://site.api.espn.com/apis/site/v2/sports/soccer/mex.1/scoreboard",
        "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard",
        "https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard",
        "https://site.api.espn.com/apis/site/v2/sports/soccer/ita.1/scoreboard",
        "https://site.api.espn.com/apis/site/v2/sports/soccer/ger.1/scoreboard",
        "https://site.api.espn.com/apis/site/v2/sports/soccer/fra.1/scoreboard"
    ]
    
    hoy = datetime.today().strftime('%Y-%m-%d')
    procesados = cargar_procesados()
    
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if "events" in data:
                for evento in data["events"]:
                    estado = evento["status"]["type"]["state"]
                    
                    if estado == "pre":
                        try:
                            competitors = evento["competitions"][0]["competitors"]
                            home_team = next(c["team"]["name"] for c in competitors if c["homeAway"] == "home")
                            away_team = next(c["team"]["name"] for c in competitors if c["homeAway"] == "away")
                            liga = data["leagues"][0]["name"]
                            
                            partido_str = f"[{liga}] LOCAL: {home_team} vs VISITANTE: {away_team}"
                            partido_id = f"{hoy}_{partido_str}"
                            
                            if partido_id not in procesados:
                                partidos.append((partido_id, partido_str))
                        except:
                            pass
        except Exception as e:
            print(f"Error al consultar ESPN: {e}")
            
    return partidos[:5]

def analizar_con_ia(historial, partido):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    
    prompt = f"""[ROL Y OBJETIVO]
    Eres un Analista Cuantitativo (EDGE BOT PRO).
    Lee este historial de reglas:
    {historial}
    
    Analiza este partido: {partido}
    
    [REGLAS VITALES DE CÁLCULO]
    1. NO INVENTES EL EDGE.
    2. Calcula la PROBABILIDAD REAL (X%).
    3. Calcula la CUOTA MÍNIMA RENTABLE dividiendo 100 entre tu Probabilidad.
    4. Si no hay valor claro, tu Veredicto DEBE ser DESCARTADO. Sé muy estricto.[FORMATO DE SALIDA ESTRICTO]
    PROHIBIDO escribir párrafos.
    Responde EXACTAMENTE con esta estructura de 6 líneas:

    🔍 REGLAS ACTIVADAS: [Nombra las reglas del historial que usaste]
    🧠 ANÁLISIS: [1 sola oración técnica explicando el pick]
    📌 PICK SUGERIDO:[Dime EXACTAMENTE a qué apostar]
    🎯 PROBABILIDAD REAL: [X%]
    💰 CUOTA MÍNIMA (+EV): [Calcula: 100 / X]
    ⚖️ VEREDICTO: [APROBADO o DESCARTADO]
    """
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages":[
            {"role": "system", "content": "Eres un bot matemático. Eres frío, directo y descartas apuestas si no hay valor matemático claro."},
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
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"❌ Excepción al enviar a Telegram: {e}")

def main():
    print("Iniciando Edge Bot Pro (Escaneo Horario)...")
    
    historial = leer_aprendizaje()
    partidos_nuevos = obtener_partidos_hoy()
    
    if not partidos_nuevos:
        print("No hay partidos nuevos sin procesar en esta hora.")
        return
        
    for partido_id, partido_str in partidos_nuevos:
        print(f"Analizando: {partido_str}")
        analisis = analizar_con_ia(historial, partido_str)
        
        guardar_procesado(partido_id)
        
        if "APROBADO" in analisis.upper():
            # Guardamos la predicción en secreto para auditarla cuando termine el partido
            guardar_prediccion_pendiente(partido_id, partido_str, analisis)
            
            mensaje_final = f"""🤖 𝗘𝗗𝗚𝗘 𝗕𝗢𝗧 𝗣𝗥𝗢 (Alerta de Valor)
━━━━━━━━━━━━━━━━━━━━
⚽ 𝗣𝗔𝗥𝗧𝗜𝗗𝗢:
{partido_str}

{analisis}
━━━━━━━━━━━━━━━━━━━━"""
            enviar_telegram(mensaje_final)
            print("✅ Pick APROBADO enviado a Telegram y guardado para auditoría.")
        else:
            print("❌ Pick DESCARTADO por la IA.")
            
        time.sleep(3)
        
    print("Escaneo finalizado.")

if __name__ == "__main__":
    main()
