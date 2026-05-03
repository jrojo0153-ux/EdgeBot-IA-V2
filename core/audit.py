"""Sistema de auditoría y aprendizaje para EdgeBot-IA-V2"""
from utils.logger import log_info, log_error, log_debug
from utils.data_manager import DataManager
from utils.api_client import ESPNClient, GroqClient


class AuditManager:
    """Gestiona la auditoría de predicciones y generación de nuevas reglas."""
    
    def __init__(self):
        log_info("AuditManager inicializado")
    
    def obtener_resultados_finalizados(self):
        """Obtiene resultados de partidos finalizados."""
        log_info("Obteniendo resultados finalizados...")
        return ESPNClient.obtener_resultados_finalizados()
    
    def auditar_predicciones(self):
        """Audita las predicciones pendientes contra resultados reales."""
        log_info("Iniciando auditoría de predicciones...")
        
        pendientes = DataManager.cargar_predicciones_pendientes()
        if not pendientes:
            log_info("No hay predicciones pendientes para auditar")
            return
        
        resultados = self.obtener_resultados_finalizados()
        claves_a_borrar = []
        nuevas_reglas = []
        
        for resultado in resultados:
            home, away, marcador = resultado
            
            for p_id, p_data in pendientes.items():
                if home in p_data["partido_str"] and away in p_data["partido_str"]:
                    log_info(f"Auditando: {marcador}")
                    
                    auditoria = GroqClient.auditar_resultado(
                        p_data["partido_str"],
                        p_data["analisis"],
                        marcador
                    )
                    
                    if auditoria:
                        # Guardar en historial
                        DataManager.agregar_historial_resultado(f"\n--- AUDITORÍA ---\nPartido: {marcador}\n{auditoria}")
                        
                        # Extraer reglas
                        for linea in auditoria.split("\n"):
                            if "REGLA:" in linea.upper():
                                regla = linea.replace('REGLA:', '').strip()
                                nuevas_reglas.append(regla)
                    
                    claves_a_borrar.append(p_id)
        
        # Actualizar predicciones pendientes
        for clave in claves_a_borrar:
            del pendientes[clave]
        
        DataManager.actualizar_predicciones_pendientes(pendientes)
        
        # Inyectar nuevas reglas
        if nuevas_reglas:
            DataManager.agregar_a_aprendizaje(nuevas_reglas)
            log_info(f"✅ Se inyectaron {len(nuevas_reglas)} nuevas reglas al modelo")
        else:
            log_info("No se generaron nuevas reglas en este ciclo")
    
    def ejecutar(self):
        """Ejecuta el ciclo completo de auditoría."""
        log_info("=" * 50)
        log_info("Iniciando Auditoría y Aprendizaje")
        log_info("=" * 50)
        
        try:
            self.auditar_predicciones()
            log_info("Auditoría completada exitosamente")
        except Exception as e:
            log_error(f"Error durante auditoría: {e}")
        
        log_info("=" * 50)
