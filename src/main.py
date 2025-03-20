from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
import yaml
import os
import uvicorn
from core.config import settings
from core.logging import get_logger, setup_logging
from api.routes import router
from services.licitacion_service import LicitacionService
from services.llm_service import LLMService
import logging

# Configuración del logger
logger = logging.getLogger(__name__)

# Variables globales para servicios
llm_service = None
licitacion_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manejador del ciclo de vida de la aplicación.
    Inicializa los servicios y recursos necesarios.
    """
    global llm_service, licitacion_service
    
    # Configuración al inicio
    setup_logging()
    logger.info("Iniciando aplicación...")
    
    # Inicializar servicios
    try:
        llm_service = LLMService(testing=True)
        licitacion_service = LicitacionService(llm_service, testing=True)
        logger.info("Servicios inicializados correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar servicios: {str(e)}")
        raise
    
    yield
    
    # Limpieza al cierre
    try:
        logger.info("Cerrando aplicación...")
        # Aquí puedes agregar código de limpieza si es necesario
    except Exception as e:
        logger.error(f"Error al cerrar la aplicación: {str(e)}")

# Crear la aplicación FastAPI
app = FastAPI(
    title="MP-RAG API",
    description="API para procesamiento de licitaciones con IA",
    version="1.0.0",
    docs_url=None,  # Deshabilitamos la UI de Swagger por defecto
    redoc_url=None,  # Deshabilitamos ReDoc por defecto
    lifespan=lifespan
)

# Configurar CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost,http://localhost:3000").split(",")
if os.getenv("ADDITIONAL_CORS_ORIGINS"):
    origins.extend(os.getenv("ADDITIONAL_CORS_ORIGINS").split(","))

# Asegurar que los orígenes estén limpios y sean únicos
origins = list(set([origin.strip() for origin in origins if origin.strip()]))


app.add_middleware(
    CORSMiddleware,
    #allow_origins=origins, #TODO: Descomentar para producción
    allow_origins=["*"], #TODO: Comentar para producción    
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600  # Aumentado a 1 hora para mejor rendimiento
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Incluir rutas
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "MP-RAG API - Bienvenido al servicio de procesamiento de licitaciones"}

@app.options("/")
async def root_options():
    """
    Endpoint para manejar solicitudes OPTIONS en la raíz.
    Necesario para CORS preflight requests.
    """
    return {}

def get_licitacion_service():
    """
    Función para obtener una instancia de LicitacionService.
    Se asegura de que los servicios se inicialicen con el modo testing correcto.
    """
    try:
        llm_service = LLMService(testing=True)
        return LicitacionService(llm_service, testing=True)
    except Exception as e:
        logger.error(f"Error al crear servicio de licitación: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al inicializar el servicio")

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """
    Endpoint personalizado para la documentación Swagger UI
    """
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="MP-RAG API - Documentación",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )

@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_schema():
    """
    Endpoint que devuelve el esquema OpenAPI de la API
    """
    try:
        # Leer el esquema desde el archivo YAML
        yaml_path = os.path.join("docs", "openapi.yaml")
        if os.path.exists(yaml_path):
            with open(yaml_path, "r") as f:
                yaml_content = yaml.safe_load(f)
                return yaml_content
        
        # Si no existe el archivo YAML, generar el esquema dinámicamente
        return get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes
        )
    except Exception as e:
        logger.error(f"Error al generar esquema OpenAPI: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al generar documentación")

def run_app():
    """
    Función principal para ejecutar la aplicación
    """
    try:
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=int(settings.PORT),
            log_level="info",
            reload=settings.DEBUG,
            workers=1  # Aseguramos un solo worker para evitar problemas de concurrencia
        )
        server = uvicorn.Server(config)
        server.run()
    except Exception as e:
        logger.error(f"Error al iniciar la aplicación: {str(e)}")
        raise

if __name__ == "__main__":
    run_app()

