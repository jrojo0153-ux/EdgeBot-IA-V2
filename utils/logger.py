"""Sistema de logging centralizado para EdgeBot-IA-V2"""
import logging
import os
from datetime import datetime
from typing import Optional


class BotException(Exception):
    """Excepción personalizada del bot."""
    pass


class Logger:
    """Gestor centralizado de logs."""
    
    _logger: Optional[logging.Logger] = None
    
    @classmethod
    def get_logger(cls) -> logging.Logger:
        """Obtiene o crea el logger singleton."""
        if cls._logger is None:
            cls._logger = cls._setup_logger()
        return cls._logger
    
    @staticmethod
    def _setup_logger() -> logging.Logger:
        """Configura el logger con handlers de consola y archivo.
        
        NOTA: Import local de Settings para evitar circular dependency.
        """
        from config.settings import Settings
        
        Settings.crear_directorios()
        
        logger = logging.getLogger('EdgeBot')
        logger.setLevel(logging.DEBUG)
        
        # Evitar duplicar handlers si ya existe
        if logger.handlers:
            return logger
        
        # Formato
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler de consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Handler de archivo
        log_file = os.path.join(
            Settings.LOGS_DIR,
            f'edgebot_{datetime.now().strftime("%Y%m%d")}.log'
        )
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger


def log_info(message: str):
    """Log de información."""
    Logger.get_logger().info(message)


def log_error(message: str):
    """Log de error."""
    Logger.get_logger().error(message)


def log_debug(message: str):
    """Log de debug."""
    Logger.get_logger().debug(message)
