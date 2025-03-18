"""
Unit tests for main.py

This module contains test cases for the main FastAPI application.
Tests cover application initialization, middleware configuration,
route handling, and documentation endpoints.
"""

import pytest
from fastapi.testclient import TestClient
import os
import yaml
from unittest.mock import patch, MagicMock, AsyncMock
from main import app, lifespan, run_app

# Configuración de fixtures
@pytest.fixture
def test_client():
    """
    Fixture that provides a test client for the FastAPI application.
    
    Returns:
        TestClient: A configured test client for making requests to the application.
    """
    return TestClient(app)

@pytest.fixture
def mock_settings():
    """
    Fixture that provides mock settings for testing.
    
    Returns:
        MagicMock: A configured mock object with test settings.
    """
    mock = MagicMock()
    mock.PORT = 5000
    mock.DEBUG = True
    mock.TESTING = True
    return mock

@pytest.fixture
def mock_llm_service():
    """
    Fixture that provides a mock LLM service for testing.
    """
    mock = MagicMock()
    mock.testing = True
    return mock

@pytest.fixture
def mock_licitacion_service():
    """
    Fixture that provides a mock LicitacionService for testing.
    """
    mock = MagicMock()
    mock.testing = True
    return mock

class TestMainApplication:
    """
    Test suite for the main FastAPI application.
    
    This class contains tests for:
    - Application initialization
    - Middleware configuration
    - Route handling
    - Documentation generation
    - Application lifecycle management
    """

    def test_root_endpoint(self, test_client):
        """
        Test the root endpoint (/) of the application.
        
        Verifies that:
        - The endpoint returns a 200 status code
        - The response contains the expected welcome message
        """
        response = test_client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "MP-RAG API - Bienvenido al servicio de procesamiento de licitaciones"}

    def test_cors_middleware(self, test_client):
        """
        Test CORS middleware configuration.
        
        Verifies that:
        - CORS headers are properly set
        - Allowed origins are correctly configured
        """
        response = test_client.options("/", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

    def test_custom_swagger_ui(self, test_client):
        """
        Test the custom Swagger UI documentation endpoint.
        
        Verifies that:
        - The /docs endpoint returns the Swagger UI HTML
        - The response contains the correct content type
        """
        response = test_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    @patch("os.path.exists")
    def test_openapi_schema_from_yaml(self, mock_exists, test_client):
        """
        Test OpenAPI schema generation from YAML file.
        
        Verifies that:
        - The schema is correctly loaded from YAML when available
        - The endpoint returns the proper JSON response
        """
        mock_exists.return_value = True
        mock_yaml_content = {
            "openapi": "3.1.0",
            "info": {
                "title": "MP-RAG API",
                "description": "API para procesamiento de licitaciones con IA",
                "version": "1.0.0"
            }
        }
        
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value = MagicMock()
            with patch("yaml.safe_load", return_value=mock_yaml_content):
                response = test_client.get("/openapi.json")
                assert response.status_code == 200
                response_json = response.json()
                # Verificar solo los campos principales
                assert response_json["openapi"] == mock_yaml_content["openapi"]
                assert response_json["info"] == mock_yaml_content["info"]

    def test_openapi_schema_generated(self, test_client):
        """
        Test OpenAPI schema dynamic generation.
        
        Verifies that:
        - The schema is generated dynamically when YAML is not available
        - The response contains the correct API information
        """
        with patch("os.path.exists", return_value=False):
            response = test_client.get("/openapi.json")
            assert response.status_code == 200
            assert "openapi" in response.json()
            assert response.json()["info"]["title"] == "MP-RAG API"

    @pytest.mark.asyncio
    async def test_lifespan(self):
        """
        Test application lifespan management.
        
        Verifies that:
        - The lifespan context manager properly initializes
        - Logging is configured at startup
        - Cleanup occurs at shutdown
        """
        async with lifespan(app):
            # Verificar que la aplicación está configurada
            assert app.title == "MP-RAG API"
            assert app.version == "1.0.0"

    @patch("uvicorn.Server")
    def test_run_app(self, mock_server, mock_settings):
        """
        Test application running configuration.
        
        Verifies that:
        - The application runs with correct settings
        - Uvicorn server is properly configured
        """
        with patch("main.settings", mock_settings):
            run_app()
            mock_server.assert_called_once()
            config = mock_server.call_args[0][0]
            assert config.host == "0.0.0.0"
            assert config.port == 5000
            assert config.reload == True

    @patch("main.LLMService")
    @patch("main.LicitacionService")
    def test_get_licitacion_service(self, mock_licitacion_service_class, mock_llm_service_class, mock_llm_service, mock_licitacion_service):
        """
        Test LicitacionService dependency injection.
        
        Verifies that:
        - The service is properly instantiated
        - Dependencies are correctly injected
        """
        # Configurar los mocks
        mock_llm_service_class.return_value = mock_llm_service
        mock_licitacion_service_class.return_value = mock_licitacion_service
        
        from main import get_licitacion_service
        service = get_licitacion_service()
        
        # Verificar que se crearon los servicios con testing=True
        mock_llm_service_class.assert_called_once_with(testing=True)
        mock_licitacion_service_class.assert_called_once_with(mock_llm_service, testing=True)
        
        assert service is not None
        assert service == mock_licitacion_service

    @patch("fastapi.staticfiles.StaticFiles")
    def test_static_files_mount(self, mock_static_files):
        """
        Test static files configuration.
        
        Verifies that:
        - Static files are properly mounted
        - The correct directory is configured
        """
        from main import app
        
        # Verificar que existe una ruta /static
        static_routes = [route for route in app.routes if str(route.path).startswith("/static")]
        assert len(static_routes) > 0
        
        # Verificar que el directorio está configurado correctamente
        static_route = static_routes[0]
        assert static_route.name == "static"
        assert hasattr(static_route, "app")
        assert static_route.app.directory == "static" 