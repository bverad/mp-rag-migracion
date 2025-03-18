import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from api.routes import router
from services.licitacion_service import LicitacionService
from services.llm_service import LLMService

class TestEndpoints:
    @pytest.fixture
    def client(self):
        return TestClient(router)

    @pytest.fixture
    def mock_licitacion_service(self):
        with patch('api.routes.LicitacionService') as mock:
            instance = mock.return_value
            instance.procesar_licitaciones = AsyncMock()
            instance.procesar_consulta_chatbot = AsyncMock()
            instance.repository = MagicMock()
            instance.repository.obtener_documentos_procesados = AsyncMock()
            yield instance

    def test_chatbotia_endpoint_success(self, client, mock_licitacion_service):
        # Configurar el mock
        mock_licitacion_service.procesar_consulta_chatbot.return_value = "Respuesta de prueba"
        
        # Realizar la solicitud
        response = client.post(
            "/chatbotia",
            json={"codigo_licitacion": "test123", "mensaje": "test message"}
        )
        
        # Verificar respuesta
        assert response.status_code == 200
        assert response.json() == {
            "message": "Procesamiento completado",
            "resultado": "Respuesta de prueba"
        }

    def test_chatbotia_endpoint_not_found(self, client, mock_licitacion_service):
        # Configurar el mock para retornar None
        mock_licitacion_service.procesar_consulta_chatbot.return_value = None
        
        # Realizar la solicitud
        response = client.post(
            "/chatbotia",
            json={"codigo_licitacion": "test123", "mensaje": "test message"}
        )
        
        # Verificar respuesta
        assert response.status_code == 404
        assert response.json() == {
            "message": "No se encontró información para la licitación especificada"
        }

    def test_procesar_licitaciones_endpoint_success(self, client, mock_licitacion_service):
        # Configurar el mock
        mock_resultado = {
            "total_procesadas": 2,
            "exitosas": 1,
            "existentes": 1,
            "con_error": 0,
            "tiempo_ejecucion": "1.23s",
            "resultados": [
                {
                    "codigo_licitacion": "test1",
                    "estado": "exitoso",
                    "resultado": {"data": "test1"}
                },
                {
                    "codigo_licitacion": "test2",
                    "estado": "existente",
                    "resultado": {"data": "test2"}
                }
            ]
        }
        mock_licitacion_service.procesar_licitaciones.return_value = mock_resultado
        
        # Realizar la solicitud sin códigos específicos (procesar todas)
        response = client.post("/resumenes_licitacion")
        
        # Verificar respuesta
        assert response.status_code == 200
        assert response.json() == {
            "message": "Procesamiento completado",
            "estadisticas": {
                "total_procesadas": 2,
                "exitosas": 1,
                "existentes": 1,
                "con_error": 0,
                "tiempo_ejecucion": "1.23s"
            },
            "resultados": mock_resultado["resultados"]
        }

    def test_procesar_licitaciones_endpoint_specific_codes(self, client, mock_licitacion_service):
        # Configurar el mock
        mock_resultado = {
            "total_procesadas": 1,
            "exitosas": 1,
            "existentes": 0,
            "con_error": 0,
            "tiempo_ejecucion": "0.5s",
            "resultados": [
                {
                    "codigo_licitacion": "test1",
                    "estado": "exitoso",
                    "resultado": {"data": "test1"}
                }
            ]
        }
        mock_licitacion_service.procesar_licitaciones.return_value = mock_resultado
        
        # Realizar la solicitud con códigos específicos
        response = client.post(
            "/resumenes_licitacion",
            json={"codigos_licitacion": ["test1"]}
        )
        
        # Verificar respuesta
        assert response.status_code == 200
        assert response.json() == {
            "message": "Procesamiento completado",
            "estadisticas": {
                "total_procesadas": 1,
                "exitosas": 1,
                "existentes": 0,
                "con_error": 0,
                "tiempo_ejecucion": "0.5s"
            },
            "resultados": mock_resultado["resultados"]
        }

    def test_procesar_licitaciones_endpoint_error(self, client, mock_licitacion_service):
        # Configurar el mock para lanzar una excepción
        mock_licitacion_service.procesar_licitaciones.side_effect = ValueError("Error de prueba")
        
        # Realizar la solicitud
        response = client.post("/resumenes_licitacion")
        
        # Verificar respuesta
        assert response.status_code == 500
        assert response.json() == {
            "message": "Error en procesamiento de licitaciones",
            "error": "Error de prueba"
        } 