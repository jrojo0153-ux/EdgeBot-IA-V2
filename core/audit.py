"""Sistema de auditoría y aprendizaje para EdgeBot-IA-V2"""
from typing import List, Dict
from utils.logger import log_info, log_error, log_debug
from utils.data_manager import DataManager
from utils.api_client import ESPNClient, GroqClient, TelegramClient
from config.settings import Settings  # ✅ AGREGADO


class AuditManager:
    """Gestiona la auditoría de predicciones y generación de nuevas reglas."""
    
    def __init__(self):
        """Inicializa el AuditManager con validación de configuración."""
        if not Settings.inicializar():
            raise ValueError("Configuración inválida. Revisa las variables de entorno.")
        DataManager.inicializar_db()
        log_info("AuditManager inicializado")
    
    def obtener_resultados_finalizados(self) -> List[tuple]:
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
        claves_a_borrar: List[str] = []
        nuevas_reglas: List[str] = []
        metricas = DataManager.obtener_metricas()
        
        for resultado in resultados:
            home, away, marcador = resultado
            
            for p_id, p_data in pendientes.items():
                if home in p_data["partido_str"] and away in p_data["partido_str"]:
                    log_info(f"Auditando: {marcador}")
                    
                    try:
                        auditoria = GroqClient.auditar_resultado(
                            p_data["partido_str"],
                            p_data["analisis"],
                            marcador
                        )
                        
                        if auditoria:
                            # Determinar si ganó o perdió
                            if "GANADA" in auditoria.upper():
                                DataManager.actualizar_metricas(
                                    apuestas_ganadas=metricas.get("apuestas_ganadas", 0) + 1
                                )
                            elif "PERDIDA" in auditoria.upper():
                                DataManager.actualizar_metricas(
                                    apuestas_perdidas=metricas.get("apuestas_perdidas", 0) + 1
                                )
                            
                            # Guardar en historial
                            DataManager.agregar_historial_resultado(
                                p_data["partido_str"],
                                marcador,
                                auditoria
                            )
                            
                            # Extraer reglas
                            for linea in auditoria.split("\n"):
                                if "REGLA:" in linea.upper():
                                    regla = linea.replace('REGLA:', '').strip()
                                    nuevas_reglas.append(regla)
                    
                    except Exception as e:
                        log_error(f"Error auditando {p_id}: {e}")
                    
                    claves_a_borrar.append(p_id)
        
        # Actualizar predicciones pendientes
        for clave in claves_a_borrar:
            DataManager.eliminar_prediccion(clave)
        
        # Inyectar nuevas reglas
        if nuevas_reglas:
            DataManager.agregar_a_aprendizaje(nuevas_reglas)
            log_info(f"✅ Se inyectaron {len(nuevas_reglas)} nuevas reglas al modelo")
            
            # Notificar por Telegram
            mensaje = f"""🎓 𝗔𝗖𝗧𝗨𝗔𝗟𝗜𝗭𝗔𝗖𝗜Ó𝗡 𝗗𝗘 𝗠𝗢𝗗𝗘𝗟𝗢
━━━━━━━━━━━━━━━━━━━━
Se aprendieron {len(nuevas_reglas)} nuevas reglas:

"""
            for i, regla in enumerate(nuevas_reglas[:5], 1):
                mensaje += f"{i}. {regla}\n"
            
            mensaje += f"\n━━━━━━━━━━━━━━━━━━━━\nROI Actual: {DataManager.calcular_roi():.2f}%"
            TelegramClient.enviar_mensaje(mensaje)
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
            raise
        
        log_info("=" * 50)
