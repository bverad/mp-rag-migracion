import logging
from datetime import datetime
import os
from logging.handlers import RotatingFileHandler
import sys
import time
from pathlib import Path

# Variable global para controlar la inicialización
_logging_initialized = False

def setup_logging():
    """Configura el sistema de logging"""
    global _logging_initialized
    
    if _logging_initialized:
        return
        
    # Crear directorio de logs si no existe
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configurar el formato de los logs
    log_format = "%(asctime)s [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Configurar el handler para archivo
    log_file = log_dir / "mp_rag.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Configurar el handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Configurar el logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Limpiar handlers existentes
    root_logger.handlers.clear()
    
    # Agregar los nuevos handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Marcar como inicializado
    _logging_initialized = True
    
    # Log inicial
    root_logger.info("=== Iniciando MP-RAG Application ===")
    root_logger.info(f"Log file: {log_file}")
    root_logger.info(f"Project root: {Path.cwd()}")

def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger con el nombre especificado"""
    if not _logging_initialized:
        setup_logging()
    return logging.getLogger(name)

# Solo configurar logging si no está inicializado
if not _logging_initialized:
    setup_logging() 