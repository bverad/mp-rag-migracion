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

# Cargar variables de entorno desde el archivo .env
env_path = find_dotenv()
if not env_path:
    raise ValueError("Archivo .env no encontrado")

logger.info(f"Ruta del archivo .env: {env_path}")

# Leer el archivo .env como bytes para evitar problemas de codificación
try:
    with open(env_path, 'rb') as f:
        content = f.read().decode('utf-8')
    
    # Buscar la línea que contiene OPENAI_API_KEY
    import re
    match = re.search(r'^OPENAI_API_KEY=(.+)$', content, re.MULTILINE)
    if not match:
        raise ValueError("OPENAI_API_KEY no encontrada en el archivo .env")
    
    OPENAI_API_KEY_VALUE = match.group(1).strip()
    logger.info("✅ Credenciales cargadas correctamente")

except Exception as e:
    logger.error("Error al leer el archivo .env")
    raise

# Cargar el resto de variables de entorno
load_dotenv(env_path, override=True)

# Log de variables de entorno
logger.info("Variables de entorno cargadas:")
logger.info(f"PORT: {os.getenv('PORT')}")
logger.info(f"DEBUG: {os.getenv('DEBUG')}")
logger.info(f"EMPRESA_ID: {os.getenv('EMPRESA_ID')}")

class Settings(BaseSettings):
    # Configuración del modelo usando ConfigDict
    model_config = ConfigDict(
        env_file=env_path,
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
    PORT: int = 5000  # Valor por defecto

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Verificar que la API key no se haya truncado solo si no estamos en modo testing
        is_testing = os.getenv("TESTING", "False").lower() == "true" or kwargs.get("TESTING", False)
        
        # En modo testing, no validamos la longitud de la API key
        if not is_testing:
            # En producción, validamos que la API key tenga el formato correcto
            if not self.OPENAI_API_KEY.startswith("sk-"):
                raise ValueError("Error en la configuración de credenciales de autenticación: La API key debe comenzar con 'sk-'")
        
        # Configurar el puerto
        try:
            env_port = os.getenv("PORT")
            if env_port:
                self.PORT = int(env_port)
                logger.info(f"Puerto configurado desde variable de entorno: {self.PORT}")
            else:
                logger.info("No se encontró variable PORT en .env, usando valor por defecto: 5000")
        except ValueError as e:
            logger.error(f"Error al convertir el puerto a entero: {e}")
            logger.info("Usando valor por defecto: 5000")
            self.PORT = 5000

# Crear una única instancia de Settings
settings = Settings()

@lru_cache()
def get_settings():
    return settings 