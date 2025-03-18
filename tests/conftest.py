"""
Configuración global de pytest y fixtures.

Este módulo proporciona fixtures compartidos y configuración para todos los módulos de prueba.
Incluye configuración para pruebas asíncronas, mocking y dependencias comunes de prueba.
"""

import pytest
import asyncio
from typing import Generator
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import sys
import os
import tempfile
from pathlib import Path
import logging
import shutil
from fastapi import FastAPI
from services.llm_service import LLMService
from services.licitacion_service import LicitacionService
from repositories.mercadopublico_repository import MercadoPublicoRepository

# Agregar el directorio raíz al PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(autouse=True)
def setup_test_env():
    """Configura el entorno de pruebas"""
    # Configurar variables de entorno para pruebas
    os.environ["TESTING"] = "true"
    os.environ["OPENAI_API_KEY"] = "test-key-123"
    os.environ["DEBUG"] = "true"
    os.environ["PORT"] = "5000"
    os.environ["USERNAME"] = "test_user"
    os.environ["PASSWORD"] = "test_password"
    os.environ["EMPRESA_ID"] = "1"
    os.environ["PYTHONPATH"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Crear directorios necesarios si no existen
    os.makedirs("reports", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    yield
    
    # Limpiar variables de entorno después de las pruebas
    env_vars = ["TESTING", "OPENAI_API_KEY", "DEBUG", "PORT", "USERNAME", "PASSWORD", "EMPRESA_ID"]
    for var in env_vars:
        os.environ.pop(var, None)

@pytest.fixture(scope="session")
def test_project_root() -> Path:
    """
    Fixture que proporciona una ruta raíz temporal para los tests.
    Se mantiene durante toda la sesión de testing.
    """
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    try:
        # Cerrar todos los handlers de logging antes de limpiar
        logging.shutdown()
        # Intentar eliminar el directorio
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception as e:
        print(f"Warning: Could not clean up temp directory: {e}")

@pytest.fixture
def test_logs_dir(test_project_root: Path) -> Path:
    """
    Fixture que crea un directorio de logs temporal.
    Se crea nuevo para cada test que lo utilice.
    """
    logs_dir = test_project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    yield logs_dir
    # Cerrar handlers antes de limpiar
    logging.shutdown()

@pytest.fixture
def mock_async_service():
    """Proporciona un mock asíncrono para servicios"""
    return MagicMock()

@pytest.fixture
def mock_repository():
    """Proporciona un mock para el repositorio"""
    return MagicMock(spec=MercadoPublicoRepository)

@pytest.fixture
def llm_service() -> LLMService:
    """
    Fixture que proporciona una instancia de LLMService en modo testing.
    """
    return LLMService(testing=True)

@pytest.fixture
def licitacion_service(llm_service: LLMService) -> LicitacionService:
    """
    Fixture que proporciona una instancia de LicitacionService en modo testing.
    """
    return LicitacionService(llm_service, testing=True)

@pytest.fixture
def test_app() -> FastAPI:
    """
    Fixture que proporciona una instancia de FastAPI configurada para pruebas.
    """
    from src.main import app
    return app

@pytest.fixture
def client(test_app: FastAPI):
    """
    Fixture que proporciona un cliente de prueba para la API.
    """
    return TestClient(test_app)

@pytest.fixture
def sample_log_record() -> logging.LogRecord:
    """
    Fixture que proporciona un LogRecord de ejemplo para testing.
    """
    return logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_path",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )

@pytest.fixture(scope="session")
def event_loop_policy():
    """
    Configura la política del bucle de eventos para las pruebas.
    
    Returns:
        asyncio.DefaultEventLoopPolicy: La política del bucle de eventos configurada.
    """
    return asyncio.DefaultEventLoopPolicy()

@pytest.fixture(scope="session")
def mock_env_vars(monkeypatch):
    """
    Configura variables de entorno para pruebas.
    
    Args:
        monkeypatch: fixture monkeypatch de pytest
    
    Configura variables de entorno comunes utilizadas en las pruebas.
    """
    monkeypatch.setenv("PORT", "5000")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("EMPRESA_ID", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("PYTHONPATH", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def mock_logger():
    """
    Proporciona un logger simulado para pruebas.
    
    Returns:
        MagicMock: Un objeto logger simulado configurado.
    """
    return MagicMock()

def pytest_configure(config):
    """
    Realiza la configuración inicial de pytest.
    
    Args:
        config: objeto de configuración de pytest
    
    Configura marcadores y otras configuraciones de pytest.
    """
    # Configurar el scope del event_loop para toda la sesión
    config.option.asyncio_mode = "auto"
    
    # Agregar marcadores
    config.addinivalue_line(
        "markers",
        "integration: marca una prueba como prueba de integración"
    )
    config.addinivalue_line(
        "markers",
        "unit: marca una prueba como prueba unitaria"
    )

@pytest.fixture(autouse=True)
def mock_aiohttp_session():
    """
    Proporciona una sesión ClientSession de aiohttp simulada para pruebas.
    
    Este fixture se utiliza automáticamente en todas las pruebas que realizan peticiones HTTP.
    """
    with MagicMock() as mock:
        yield mock 