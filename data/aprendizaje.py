import os
import requests
import json

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def crear_reglas_base_si_no_existen():
    """Mantiene tus reglas base originales si el archivo es nuevo."""
    os.makedirs("data", exist_ok=True)
    ruta = "data/aprendizaje.txt"
    if not os.path.exists(ruta):
        contenido_base = """[HISTORIAL RECIENTE PARA APRENDIZAJE Y CALIBRACIÓN]
### REGLAS BASE
- [Away Elite Defense]: Reducir penalización a visitantes si son Top 5 europeo en PPDA.
- [Home Advantage Decay]: En eliminatorias con alto xG (>3.0), el factor cancha pierde 15%.
- [Extreme Altitude]: Multiplicar xGA del visitante por 1.35 en la 2da mitad en altitud.
- [Elite Roster Home Protection]: El Edge es penalizado si el pick va contra equipos de Élite en casa.
"""
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido_base)

def auditar_resultado_con_ia(partido_str, analisis_previo, marcador_real):
    """Pide a Groq que evalúe por qué se ganó o se perdió la predicción."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
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
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Eres un auditor de datos. Analizas victorias y derrotas de modelos predictivos deportivos."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
    except:
        pass
    return None

def ejecutar_auditoria():
    print("Iniciando auditoría de resultados pasados...")
    crear_reglas_base_si_no_existen()
    
    ruta_pendientes = "data/predicciones_pendientes.json"
    if not os.path.exists(ruta_pendientes):
        print("No hay predicciones pendientes por auditar.")
        return
        
    with open(ruta_pendientes, "r", encoding="utf-8") as f:
        pendientes = json.load(f)
        
    if not pendientes:
        print("El archivo de predicciones está vacío.")
        return

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
    
    claves_a_borrar = []
    nuevas_reglas = []
    
    # Buscar resultados en ESPN de partidos que ya terminaron
    for url in urls:
        try:
            res = requests.get(url, timeout=10)
            data = res.json()
            if "events" in data:
                for evento in data["events"]:
                    if evento["status"]["type"]["state"] == "post": # PARTIDO TERMINADO
                        comps = evento["competitions"][0]["competitors"]
                        home = next(c["team"]["name"] for c in comps if c["homeAway"] == "home")
                        away = next(c["team"]["name"] for c in comps if c["homeAway"] == "away")
                        home_sc = next(c["score"] for c in comps if c["homeAway"] == "home")
                        away_sc = next(c["score"] for c in comps if c["homeAway"] == "away")
                        
                        marcador = f"{home} {home_sc} - {away_sc} {away}"
                        
                        # Revisar si este partido lo predijimos
                        for p_id, p_data in pendientes.items():
                            if home in p_data["partido_str"] and away in p_data["partido_str"]:
                                print(f"Auditando partido finalizado: {marcador}")
                                auditoria = auditar_resultado_con_ia(p_data["partido_str"], p_data["analisis"], marcador)
                                
                                if auditoria:
                                    # Guardar en el historial permanente (Ganadoras y Perdedoras)
                                    with open("data/historial_resultados.txt", "a", encoding="utf-8") as f_hist:
                                        f_hist.write(f"\n--- AUDITORÍA ---\nPartido: {marcador}\n{auditoria}\n")
                                    
                                    # Extraer solo la regla para inyectarla al cerebro del bot
                                    for linea in auditoria.split("\n"):
                                        if "REGLA:" in linea.upper():
                                            nuevas_reglas.append(f"- {linea.replace('REGLA:', '').strip()}")
                                
                                claves_a_borrar.append(p_id)
        except Exception as e:
            pass

    # Actualizar el JSON borrando los partidos ya auditados
    for clave in claves_a_borrar:
        del pendientes[clave]
        
    with open(ruta_pendientes, "w", encoding="utf-8") as f:
        json.dump(pendientes, f, ensure_ascii=False, indent=4)
        
    # Inyectar las nuevas reglas al cerebro del bot (aprendizaje.txt)
    if nuevas_reglas:
        with open("data/aprendizaje.txt", "a", encoding="utf-8") as f_reglas:
            f_reglas.write("\n### NUEVAS REGLAS AUTOMÁTICAS\n")
            for regla in nuevas_reglas:
                f_reglas.write(regla + "\n")
        print("✅ Nuevas reglas inyectadas exitosamente al modelo.")
    else:
        print("No se generaron reglas nuevas en este ciclo.")

if __name__ == "__main__":
    ejecutar_auditoria()
