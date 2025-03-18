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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manejador del ciclo de vida de la aplicación
    """
    # Configuración al inicio
    setup_logging()
    logger.info("Iniciando aplicación...")
    yield
    # Limpieza al cierre
    logger.info("Cerrando aplicación...")

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
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://testserver"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600  # Cache preflight requests for 10 minutes
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Incluir rutas
app.include_router(router)

# Inicializar servicios
llm_service = LLMService(testing=True)
licitacion_service = LicitacionService(llm_service, testing=True)

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

# Inyección de dependencias
def get_licitacion_service():
    """
    Función para obtener una instancia de LicitacionService.
    Se asegura de que los servicios se inicialicen con el modo testing correcto.
    """
    global llm_service
    if not llm_service:
        llm_service = LLMService(testing=True)
    return LicitacionService(llm_service, testing=True)

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

# Asegurar que los servicios se inicialicen correctamente
@app.on_event("startup")
async def startup_event():
    """
    Evento de inicio de la aplicación.
    Asegura que los servicios se inicialicen correctamente.
    """
    global llm_service, licitacion_service
    if not llm_service:
        llm_service = LLMService(testing=True)
    if not licitacion_service:
        licitacion_service = LicitacionService(llm_service, testing=True)

def run_app():
    """
    Función principal para ejecutar la aplicación
    """
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",  # Host por defecto para permitir conexiones externas
        port=int(settings.PORT),  # Aseguramos que el puerto sea un entero
        log_level="info",
        reload=settings.DEBUG
    )
    server = uvicorn.Server(config)
    server.run()

if __name__ == "__main__":
    run_app()

