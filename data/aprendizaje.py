import os

def actualizar_historial_aprendizaje():
    """
    Genera y actualiza el archivo aprendizaje.txt con las últimas 
    auditorías y reglas matemáticas (Regla 4) del modelo.
    """
    # Asegurarse de que el directorio data/ exista
    directorio = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(directorio, exist_ok=True)
    ruta_txt = os.path.join(directorio, "aprendizaje.txt")
    
    contenido_aprendizaje = """[HISTORIAL RECIENTE PARA APRENDIZAJE Y CALIBRACIÓN]

### Evento 1: Sporting Lisboa 0 - 1 Arsenal (Champions League)
- Lección Extraída: El modelo sobre-penalizó al favorito visitante. La defensa de élite del Arsenal resistió las transiciones.
- Regla a Aplicar [Away Elite Defense Modifier]: Reducir la penalización a favoritos visitantes si pertenecen al Top 5 europeo en métricas de PPDA y xGA.

### Evento 2: Real Madrid 1 - 2 Bayern Munich (Champions League)
- Lección Extraída: El factor local colapsó ante la altísima varianza ofensiva del visitante en un partido de eliminación directa.
- Regla a Aplicar [Home Advantage Decay]: En eliminatorias con alto xG proyectado (>3.0), el factor cancha pierde un 15% de peso algorítmico. Exigir mayor Edge para Doble Oportunidad local.

### Evento 3: LAFC 3 - 0 Cruz Azul (Concacaf)
- Lección Extraída: Subestimación masiva de la eficiencia ofensiva de equipos top de la MLS jugando en casa frente a defensas adelantadas de la Liga MX.
- Regla a Aplicar [Transition Speed Multiplier]: Ignorar la penalización al favorito local si tiene ataque vertical rápido y enfrenta a un equipo que deja espacios a la espalda.

### Evento 4: Nashville SC 0 - 0 Club América (Concacaf)
- Lección Extraída: Sobreestimación de la capacidad del favorito visitante (América) para romper un bloque defensivo profundo y lento.
- Regla a Aplicar[Low-Block Away Decay]: Reducir el xG proyectado del visitante en un 20% cuando enfrenta bloques bajos/profundos. Favorecer el Under de goles.

### Evento 5: FC Barcelona 0 - 2 Atlético de Madrid (Champions League)
- Lección Extraída: Validación de la regla anterior. El bloque bajo de élite del Atlético forzó centros laterales ineficientes del Barcelona y rompió una racha de 14 victorias locales.
- Regla a Aplicar: Mantener el apoyo al Underdog visitante si posee una defensa top capaz de secar el TS% (True Shooting) del local.

### Evento 6: París Saint-Germain 2 - 0 Liverpool FC (Champions League)
- Lección Extraída: El modelo subestimó la resistencia a la presión del mediocampo parisino frente a la presión alta del Liverpool.
- Regla a Aplicar [Elite Press-Resistance]: Anular la regla de 'Home Advantage Decay' si el equipo local es Top 3 europeo en retención de balón bajo presión.

### Evento 7: Tigres UANL 2 - 0 Seattle Sounders (Concacaf)
- Lección Extraída: En partidos de ritmo lento, la mayor calidad de finalización del local rompe la varianza de un posible empate.
- Regla a Aplicar[Low-Pace Quality Disparity]: Descartar apostar al Empate en partidos de menos de 90 posesiones si el local tiene un xG/tiro muy superior.

### Evento 8: Deportivo Toluca 4 - 2 LA Galaxy (Concacaf)
- Lección Extraída: La altitud extrema (>2,600m) colapsa la estructura defensiva de los equipos de la MLS en la segunda mitad.
- Regla a Aplicar [Extreme Altitude Decay]: Multiplicar el xGA (Goles Esperados en Contra) del visitante por 1.35 en la segunda mitad. No apostar a hándicaps cortos a favor de equipos no aclimatados.
"""

    # Escribir el contenido en el archivo de texto
    with open(ruta_txt, "w", encoding="utf-8") as file:
        file.write(contenido_aprendizaje)
        
    print(f"✅ Archivo de aprendizaje actualizado exitosamente en: {ruta_txt}")
    print("El bot de Groq (LLaMA 3) ahora leerá este contexto antes de cada predicción.")

if __name__ == "__main__":
    actualizar_historial_aprendizaje()
