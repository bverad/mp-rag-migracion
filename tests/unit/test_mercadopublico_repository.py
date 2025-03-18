import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.repositories.mercadopublico_repository import MercadoPublicoRepository
import json
import aiohttp
from datetime import datetime

@pytest.fixture
def mock_settings():
    """Fixture que proporciona configuraciones mock para el repositorio"""
    settings = MagicMock()
    settings.BASE_URL = "http://api.test"
    settings.AUTH_URL = "http://api.test/auth"
    settings.DOCUMENTOS_PROCESADOS_URL = "http://api.test/documentos"
    settings.DOCUMENTO_CONTENT_URL = "http://api.test/contenido"
    settings.OBTENER_RESPUESTA_IA_URL = "http://api.test/respuesta"
    settings.GUARDAR_RESPUESTA_IA_URL = "http://api.test/guardar"
    settings.USERNAME = "test_user"
    settings.PASSWORD = "test_pass"
    settings.EMPRESA_ID = "123"
    return settings

@pytest.fixture
def mock_response():
    """Fixture que proporciona una respuesta mock"""
    response = MagicMock()
    response.status = 200
    response.json = AsyncMock(return_value={"token": "test_token"})
    return response

@pytest.fixture
def mock_session():
    """Fixture que proporciona una sesión mock"""
    session = MagicMock()
    session.get = AsyncMock()
    session.post = AsyncMock()
    return session

@pytest.mark.unit
class TestMercadoPublicoRepository:
    """Tests unitarios para el repositorio de Mercado Público"""

    def test_inicializacion_testing(self, mock_settings):
        """Test de inicialización en modo testing"""
        with patch('src.repositories.mercadopublico_repository.settings', mock_settings):
            repo = MercadoPublicoRepository(testing=True)
            assert repo.testing == True
            assert repo.token == "test_token"
            assert repo.base_url == mock_settings.BASE_URL
            assert "Authorization" in repo.session.headers
            assert "Content-Type" in repo.session.headers

    def test_inicializacion_produccion(self, mock_settings):
        """Test de inicialización en modo producción"""
        with patch('src.repositories.mercadopublico_repository.settings', mock_settings), \
             patch('requests.Session.post') as mock_post:
            
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"access_token": "prod_token"}
            
            repo = MercadoPublicoRepository(testing=False)
            assert repo.testing == False
            assert repo.token == "prod_token"
            assert repo.base_url == mock_settings.BASE_URL
            mock_post.assert_called_once()

    def test_autenticacion_error_response(self, mock_settings):
        """Test de autenticación con error en la respuesta"""
        with patch('src.repositories.mercadopublico_repository.settings', mock_settings), \
             patch('requests.Session.post') as mock_post:
            
            mock_post.return_value.status_code = 401
            mock_post.return_value.json.return_value = {"msg": "Error de autenticación"}
            
            with pytest.raises(ValueError, match="Error de autenticación: 401"):
                MercadoPublicoRepository(testing=False)

    def test_autenticacion_sin_token(self, mock_settings):
        """Test de autenticación cuando no se recibe token"""
        with patch('src.repositories.mercadopublico_repository.settings', mock_settings), \
             patch('requests.Session.post') as mock_post:
            
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {}
            
            with pytest.raises(ValueError, match="Respuesta vacía del servidor"):
                MercadoPublicoRepository(testing=False)

    @pytest.mark.asyncio
    async def test_obtener_documentos_procesados_testing(self, mock_settings):
        """Test de obtención de documentos en modo testing"""
        with patch('src.repositories.mercadopublico_repository.settings', mock_settings):
            repo = MercadoPublicoRepository(testing=True)
            resultado = await repo.obtener_documentos_procesados()
            assert resultado == {"test_code": ["test_path"]}

    @pytest.mark.asyncio
    async def test_obtener_documentos_procesados_exito(self, mock_settings, mock_session, mock_response):
        """Test de obtención de documentos exitosa"""
        # Mock para la autenticación
        auth_response = MagicMock()
        auth_response.status_code = 200
        auth_response.json.return_value = {"access_token": "test_token"}
        
        # Mock para la respuesta de documentos
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[
            {"codigo_licitacion": "123", "ruta_documento": "doc1.pdf"},
            {"codigo_licitacion": "123", "ruta_documento": "doc2.pdf"},
            {"codigo_licitacion": "456", "ruta_documento": "doc3.pdf"}
        ])
        
        # Configurar el mock de la sesión aiohttp
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_session
        mock_session_context.__aexit__.return_value = None
        
        # Configurar el mock de la respuesta get
        mock_response_context = AsyncMock()
        mock_response_context.__aenter__.return_value = mock_response
        mock_response_context.__aexit__.return_value = None
        
        mock_session.get = MagicMock(return_value=mock_response_context)
        
        with patch('src.repositories.mercadopublico_repository.settings', mock_settings), \
             patch('requests.Session.post', return_value=auth_response), \
             patch('aiohttp.ClientSession', return_value=mock_session_context):
            
            repo = MercadoPublicoRepository(testing=False)
            resultado = await repo.obtener_documentos_procesados()
            
            assert "123" in resultado
            assert "456" in resultado
            assert len(resultado["123"]) == 2
            assert len(resultado["456"]) == 1
            assert "doc1.pdf" in resultado["123"]
            assert "doc2.pdf" in resultado["123"]
            assert "doc3.pdf" in resultado["456"]

    @pytest.mark.asyncio
    async def test_obtener_contenido_documento_testing(self, mock_settings):
        """Test de obtención de contenido en modo testing"""
        with patch('src.repositories.mercadopublico_repository.settings', mock_settings):
            repo = MercadoPublicoRepository(testing=True)
            resultado = await repo.obtener_contenido_documento("ruta.pdf", "123")
            assert resultado == "Test content"

    @pytest.mark.asyncio
    async def test_obtener_contenido_documento_exito(self, mock_settings, mock_session, mock_response):
        """Test de obtención de contenido exitosa"""
        # Mock para la autenticación
        auth_response = MagicMock()
        auth_response.status_code = 200
        auth_response.json.return_value = {"access_token": "test_token"}
        
        # Mock para la respuesta del contenido
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"contenido": "Contenido del documento"})
        
        # Configurar el mock de la sesión aiohttp
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_session
        mock_session_context.__aexit__.return_value = None
        
        # Configurar el mock de la respuesta get
        mock_response_context = AsyncMock()
        mock_response_context.__aenter__.return_value = mock_response
        mock_response_context.__aexit__.return_value = None
        
        mock_session.get = MagicMock(return_value=mock_response_context)
        
        with patch('src.repositories.mercadopublico_repository.settings', mock_settings), \
             patch('requests.Session.post', return_value=auth_response), \
             patch('aiohttp.ClientSession', return_value=mock_session_context):
            
            repo = MercadoPublicoRepository(testing=False)
            resultado = await repo.obtener_contenido_documento("ruta.pdf", "123")
            
            assert resultado == "Contenido del documento"
            mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_obtener_respuesta_ia_testing(self, mock_settings):
        """Test de obtención de respuesta IA en modo testing"""
        with patch('src.repositories.mercadopublico_repository.settings', mock_settings):
            repo = MercadoPublicoRepository(testing=True)
            resultado = await repo.obtener_respuesta_ia("123")
            assert resultado is None

    @pytest.mark.asyncio
    async def test_obtener_respuesta_ia_exito(self, mock_settings, mock_session, mock_response):
        """Test de obtención de respuesta IA exitosa"""
        # Mock para la autenticación
        auth_response = MagicMock()
        auth_response.status_code = 200
        auth_response.json.return_value = {"access_token": "test_token"}
        
        # Mock para la respuesta IA
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"respuesta": "Respuesta de prueba"})
        
        # Configurar el mock de la sesión aiohttp
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_session
        mock_session_context.__aexit__.return_value = None
        
        # Configurar el mock de la respuesta get
        mock_response_context = AsyncMock()
        mock_response_context.__aenter__.return_value = mock_response
        mock_response_context.__aexit__.return_value = None
        
        mock_session.get = MagicMock(return_value=mock_response_context)
        
        with patch('src.repositories.mercadopublico_repository.settings', mock_settings), \
             patch('requests.Session.post', return_value=auth_response), \
             patch('aiohttp.ClientSession', return_value=mock_session_context):
            
            repo = MercadoPublicoRepository(testing=False)
            resultado = await repo.obtener_respuesta_ia("123")
            
            assert resultado == {"respuesta": "Respuesta de prueba"}
            mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_obtener_respuesta_ia_no_encontrada(self, mock_settings, mock_session, mock_response):
        """Test de obtención de respuesta IA cuando no existe"""
        # Mock para la autenticación
        auth_response = MagicMock()
        auth_response.status_code = 200
        auth_response.json.return_value = {"access_token": "test_token"}
        
        # Mock para la respuesta IA
        mock_response.status = 404
        mock_response.json = AsyncMock(return_value={"error": "No encontrado"})
        
        # Configurar el mock de la sesión aiohttp
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_session
        mock_session_context.__aexit__.return_value = None
        
        # Configurar el mock de la respuesta get
        mock_response_context = AsyncMock()
        mock_response_context.__aenter__.return_value = mock_response
        mock_response_context.__aexit__.return_value = None
        
        mock_session.get = MagicMock(return_value=mock_response_context)
        
        with patch('src.repositories.mercadopublico_repository.settings', mock_settings), \
             patch('requests.Session.post', return_value=auth_response), \
             patch('aiohttp.ClientSession', return_value=mock_session_context):
            
            repo = MercadoPublicoRepository(testing=False)
            resultado = await repo.obtener_respuesta_ia("123")
            
            assert resultado is None
            mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_guardar_respuesta_ia_testing(self, mock_settings):
        """Test de guardado de respuesta IA en modo testing"""
        with patch('src.repositories.mercadopublico_repository.settings', mock_settings):
            repo = MercadoPublicoRepository(testing=True)
            resultado = await repo.guardar_respuesta_ia("123", '{"respuesta": "test"}')
            assert resultado is True

    @pytest.mark.asyncio
    async def test_guardar_respuesta_ia_exito(self, mock_settings, mock_session, mock_response):
        """Test de guardado de respuesta IA exitoso"""
        # Mock para la autenticación
        auth_response = MagicMock()
        auth_response.status_code = 200
        auth_response.json.return_value = {"access_token": "test_token"}
        
        # Mock para la respuesta del guardado
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"mensaje": "Guardado exitoso"})
        
        # Configurar el mock de la sesión aiohttp
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_session
        mock_session_context.__aexit__.return_value = None
        
        # Configurar el mock de la respuesta post
        mock_response_context = AsyncMock()
        mock_response_context.__aenter__.return_value = mock_response
        mock_response_context.__aexit__.return_value = None
        
        mock_session.post = MagicMock(return_value=mock_response_context)
        
        with patch('src.repositories.mercadopublico_repository.settings', mock_settings), \
             patch('requests.Session.post', return_value=auth_response), \
             patch('aiohttp.ClientSession', return_value=mock_session_context):
            
            repo = MercadoPublicoRepository(testing=False)
            resultado = await repo.guardar_respuesta_ia("123", "Análisis de prueba")
            
            assert resultado is True
            mock_session.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_guardar_respuesta_ia_error(self, mock_settings, mock_session, mock_response):
        """Test de guardado de respuesta IA con error"""
        # Mock para la autenticación
        auth_response = MagicMock()
        auth_response.status_code = 200
        auth_response.json.return_value = {"access_token": "test_token"}
        
        # Mock para la respuesta del guardado
        mock_response.status = 500
        mock_response.json = AsyncMock(return_value={"error": "Error interno del servidor"})
        
        # Configurar el mock de la sesión aiohttp
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_session
        mock_session_context.__aexit__.return_value = None
        
        # Configurar el mock de la respuesta post
        mock_response_context = AsyncMock()
        mock_response_context.__aenter__.return_value = mock_response
        mock_response_context.__aexit__.return_value = None
        
        mock_session.post = MagicMock(return_value=mock_response_context)
        
        with patch('src.repositories.mercadopublico_repository.settings', mock_settings), \
             patch('requests.Session.post', return_value=auth_response), \
             patch('aiohttp.ClientSession', return_value=mock_session_context):
            
            repo = MercadoPublicoRepository(testing=False)
            resultado = await repo.guardar_respuesta_ia("123", "Análisis de prueba")
            
            assert resultado is False
            mock_session.post.assert_called_once()

    def test_make_request_reautenticacion(self, mock_settings):
        """Test de reautenticación en _make_request"""
        with patch('src.repositories.mercadopublico_repository.settings', mock_settings), \
             patch('requests.Session.request') as mock_request, \
             patch('requests.Session.post') as mock_post:
            
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"access_token": "new_token"}
            mock_request.return_value.status_code = 200
            mock_request.return_value.json.return_value = {"data": "test"}
            
            repo = MercadoPublicoRepository(testing=False)
            repo.token_expiry = datetime.now().timestamp() - 3600  # Token expirado
            
            resultado = repo._make_request("GET", "http://test.url")
            
            assert resultado == {"data": "test"}
            assert mock_post.call_count == 2  # Una vez en init y otra en reautenticación
            assert mock_request.call_count == 1 