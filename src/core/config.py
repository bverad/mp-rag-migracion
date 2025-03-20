import os
from dotenv import load_dotenv, find_dotenv
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache
import logging
from typing import ClassVar, Optional
from pathlib import Path

# Obtener la ruta absoluta del directorio raíz del proyecto
PROJECT_ROOT = str(Path(__file__).resolve().parents[2])

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Intentar cargar variables de entorno desde el archivo .env si existe
env_path = find_dotenv(usecwd=True)
if env_path:
    logger.info(f"Archivo .env encontrado en: {env_path}")
    load_dotenv(env_path, override=True)
    
    # Leer el archivo .env como bytes para evitar problemas de codificación
    try:
        with open(env_path, 'rb') as f:
            content = f.read().decode('utf-8')
        
        # Buscar la línea que contiene OPENAI_API_KEY
        import re
        match = re.search(r'^OPENAI_API_KEY=(.+)$', content, re.MULTILINE)
        if match:
            OPENAI_API_KEY_VALUE = match.group(1).strip()
            logger.info("✅ Credenciales cargadas desde archivo .env")
    except Exception as e:
        logger.warning(f"No se pudo leer el archivo .env: {str(e)}")
else:
    logger.info("No se encontró archivo .env, usando variables de entorno del sistema")

# Log de variables de entorno importantes
logger.info("Variables de entorno cargadas:")
logger.info(f"PORT: {os.getenv('PORT')}")
logger.info(f"DEBUG: {os.getenv('DEBUG')}")
logger.info(f"EMPRESA_ID: {os.getenv('EMPRESA_ID')}")

class Settings(BaseSettings):
    # Configuración del modelo usando ConfigDict
    model_config = ConfigDict(
        case_sensitive=True,
        extra="allow"
    )
    
    # Configuración de OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0"))
    
    # Configuración de la aplicación
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    TESTING: bool = os.getenv("TESTING", "False").lower() == "true"
    
    # API Base URLs
    BASE_URL: str = os.getenv("BASE_URL", "https://backendlicitaciones.activeit.com")
    API_BASE_URL: str = BASE_URL
    
    # API Endpoints
    DOCUMENTOS_PROCESADOS_URL: str = f"{BASE_URL}/documentos/documentos_procesados"
    DOCUMENTO_CONTENT_URL: str = f"{BASE_URL}/documentos/documentos_procesados/content"
    GUARDAR_RESPUESTA_IA_URL: str = f"{BASE_URL}/ia/guardar_respuesta_ia"
    OBTENER_RESPUESTA_IA_URL: str = f"{BASE_URL}/ia/obtener_respuesta_ia"
    
    # Auth Settings
    AUTH_URL: str = f"{BASE_URL}/auth/login"
    USERNAME: str = os.getenv("USERNAME", "admin")
    PASSWORD: str = os.getenv("PASSWORD", "password")
    EMPRESA_ID: int = int(os.getenv("EMPRESA_ID", "1"))
    
    # App Settings
    BASE_DIR: str = PROJECT_ROOT
    LOGS_DIR: str = os.path.join(BASE_DIR, "logs")
    
    # Puerto de la aplicación
    PORT: int = int(os.getenv("PORT", "5000"))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Verificar que la API key no se haya truncado solo si no estamos en modo testing
        is_testing = os.getenv("TESTING", "False").lower() == "true" or kwargs.get("TESTING", False)
        
        # En modo testing o si estamos en un entorno que no requiere validación, no validamos la API key
        if not is_testing and os.getenv("APP_ENV") != "production":
            # Solo validamos el formato de la API key en desarrollo
            if not self.OPENAI_API_KEY.startswith("sk-"):
                raise ValueError("Error en la configuración de credenciales de autenticación: La API key debe comenzar con 'sk-'")
        
        logger.info(f"Aplicación configurada en puerto: {self.PORT}")

# Crear una única instancia de Settings
settings = Settings()

@lru_cache()
def get_settings():
    return settings 