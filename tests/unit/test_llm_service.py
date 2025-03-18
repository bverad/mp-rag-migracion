import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.llm_service import LLMService
from src.core.config import Settings
from langchain.schema.runnable import RunnablePassthrough
import os
import json

@pytest.fixture
def llm_service():
    """Fixture para modo testing"""
    service = LLMService(testing=True)
    
    # Crear nuevos mocks para cada chain
    service.chain_0 = AsyncMock()
    service.chain_1 = AsyncMock()
    service.chain_2 = AsyncMock()
    
    # Configurar las respuestas específicas para cada mock
    service.chain_0.ainvoke.return_value = "Test resumen"
    service.chain_1.ainvoke.return_value = '{"respuestaIA":[{"resumen":"Test resumen"}]}'
    service.chain_2.ainvoke.return_value = "Test response"
    
    # Configurar llm para fallback
    service.llm_2 = AsyncMock()
    service.llm_2.agenerate.return_value.generations = [[AsyncMock(text="Fallback response")]]
    
    return service

@pytest.fixture
def llm_service_prod():
    """Fixture para modo producción con API key válida"""
    settings = Settings(
        OPENAI_API_KEY="sk-test-mock-key-123456789",
        OPENAI_MODEL="gpt-3.5-turbo",
        OPENAI_TEMPERATURE=0.7,
        TESTING=False,
        DEBUG=False,
        PORT=8000,
        USERNAME="test_user",
        PASSWORD="test_password",
        EMPRESA_ID=1
    )
    return LLMService(testing=False, settings=settings)

@pytest.fixture
def llm_service_invalid_key():
    """Fixture para modo producción con API key inválida"""
    settings = MagicMock()
    settings.OPENAI_API_KEY = "invalid_key"
    settings.TESTING = False
    settings.DEBUG = False
    settings.PORT = 8000
    settings.USERNAME = "test_user"
    settings.PASSWORD = "test_password"
    settings.EMPRESA_ID = 1
    return LLMService(testing=False, settings=settings, validate_on_init=False)

@pytest.fixture
def llm_service_missing_key():
    """Fixture para modo producción sin API key"""
    settings = MagicMock()
    settings.OPENAI_API_KEY = None
    settings.TESTING = False
    settings.DEBUG = False
    settings.PORT = 8000
    settings.USERNAME = "test_user"
    settings.PASSWORD = "test_password"
    settings.EMPRESA_ID = 1
    return LLMService(testing=False, settings=settings, validate_on_init=False)

@pytest.fixture
def mock_settings():
    """Fixture que proporciona configuraciones mock para el servicio"""
    settings = MagicMock()
    settings.OPENAI_API_KEY = "sk-test-mock-key-123456789"  # API key de prueba genérica
    settings.OPENAI_MODEL = "gpt-4"
    settings.OPENAI_TEMPERATURE = 0.7
    return settings

@pytest.mark.unit
class TestLLMService:
    def test_inicializacion(self, llm_service):
        """Test para verificar la inicialización correcta del servicio"""
        assert llm_service.testing is True
        assert llm_service.chain_0 is not None
        assert llm_service.chain_1 is not None
        assert llm_service.chain_2 is not None
        assert isinstance(llm_service.chain_0, AsyncMock)
        assert isinstance(llm_service.chain_1, AsyncMock)
        assert isinstance(llm_service.chain_2, AsyncMock)

    @pytest.mark.asyncio
    async def test_process_resumen(self, llm_service):
        """Prueba el procesamiento de resumen"""
        input_text = "Test input"
        result = await llm_service.process_resumen(input_text)
        assert result == "Test resumen"
        llm_service.chain_0.ainvoke.assert_called_once_with({"input_text": input_text})

    @pytest.mark.asyncio
    async def test_process_unification(self, llm_service):
        """Prueba la unificación de respuestas"""
        resumen_ia = "Test resumen"
        result = await llm_service.process_unification(resumen_ia)
        assert result == '{"respuestaIA":[{"resumen":"Test resumen"}]}'
        llm_service.chain_1.ainvoke.assert_called_once_with({"resumen_ia": resumen_ia})

    @pytest.mark.asyncio
    async def test_process_chatbot_query(self, llm_service):
        """Prueba el procesamiento de consultas del chatbot"""
        input_text = "Test query"
        documentos_texto = "Test docs"
        result = await llm_service.process_chatbot_query(input_text, documentos_texto)
        assert result == "Test response"
        llm_service.chain_2.ainvoke.assert_called_once_with({
            "documentos": documentos_texto,
            "pregunta": input_text
        })

    def test_get_api_key_info_testing(self, mock_settings):
        """Test de obtención de información de API key en modo testing"""
        service = LLMService(testing=True, settings=mock_settings)
        info = service.get_api_key_info()
        assert info["status"] == "success"
        assert info["is_valid"] == True

    def test_get_api_key_info_sin_key(self, mock_settings):
        """Test de obtención de información cuando no hay API key"""
        mock_settings.OPENAI_API_KEY = None
        service = LLMService(testing=False, settings=mock_settings, validate_on_init=False)
        info = service.get_api_key_info()
        assert info["status"] == "error"
        assert info["is_valid"] == False
        assert info["message"] == "API key no configurada"

    def test_refresh_api_key_testing(self, mock_settings):
        """Test de refresh de API key en modo testing"""
        service = LLMService(testing=True, settings=mock_settings)
        service.refresh_api_key()  # No debería lanzar excepciones

    @patch('src.services.llm_service.get_settings')
    def test_refresh_api_key_produccion(self, mock_get_settings):
        """Test de refresh de API key en modo producción"""
        # Configurar una API key de prueba genérica
        test_api_key = "sk-test-mock-key-123456789"
        
        # Configurar el mock settings
        mock_settings = MagicMock()
        mock_settings.OPENAI_API_KEY = test_api_key
        mock_get_settings.return_value = mock_settings
        
        # Establecer la API key en el entorno
        os.environ["OPENAI_API_KEY"] = test_api_key
        
        # Crear el servicio
        service = LLMService(testing=False, settings=mock_settings, validate_on_init=True)
        
        # Ejecutar el refresh
        service.refresh_api_key()
        
        # Verificar que get_settings fue llamado
        mock_get_settings.assert_called_once()
        
        # Verificar que la API key no ha cambiado
        assert os.environ.get("OPENAI_API_KEY") == test_api_key

    def test_refresh_api_key_error(self, mock_settings):
        """Test de refresh de API key cuando hay error"""
        mock_settings.OPENAI_API_KEY = None
        service = LLMService(testing=False, settings=mock_settings, validate_on_init=False)
        
        # Forzar la validación de la API key antes de refrescar
        with patch.object(service, '_validate_api_key', side_effect=ValueError("OPENAI_API_KEY no está configurada")):
            with pytest.raises(ValueError, match="OPENAI_API_KEY no está configurada"):
                service.refresh_api_key()

    def test_get_api_key_info_prod_mode(self, llm_service_prod):
        """Prueba obtener información de API key en modo producción"""
        info = llm_service_prod.get_api_key_info()
        assert info["status"] == "success"
        assert info["message"] == "API key válida"
        assert info["is_valid"] is True

    def test_validate_api_key_invalid(self, llm_service_invalid_key):
        """Prueba la validación de API key con una key inválida"""
        with pytest.raises(ValueError, match="Error al validar credenciales"):
            llm_service_invalid_key._validate_api_key()

    def test_validate_api_key_missing(self, llm_service_missing_key):
        """Prueba la validación cuando falta la API key"""
        with pytest.raises(ValueError, match="OPENAI_API_KEY no está configurada"):
            llm_service_missing_key._validate_api_key()

    @patch('os.environ')
    def test_initialize_models_env_error(self, mock_env, llm_service_prod):
        """Prueba el manejo de errores al configurar variables de entorno"""
        mock_env.get.return_value = "different_key"
        with pytest.raises(ValueError, match="Error al configurar credenciales"):
            llm_service_prod._initialize_models()

    @patch('langchain_openai.ChatOpenAI')
    def test_initialize_models_llm_error(self, mock_chat_openai, llm_service_prod):
        """Prueba la inicialización de modelos cuando hay un error"""
        mock_chat_openai.side_effect = Exception("Error de inicialización")
        llm_service_prod.settings.OPENAI_MODEL = None
        with pytest.raises(ValueError, match="OPENAI_MODEL no está configurado"):
            llm_service_prod._initialize_models()

    def test_initialize_prompts_error(self, llm_service):
        """Prueba la inicialización de prompts cuando hay un error"""
        llm_service._force_prompt_error = True
        with pytest.raises(ValueError, match="Error al crear el prompt template"):
            llm_service._initialize_prompts()

    def test_initialize_chains_error(self, llm_service_prod):
        """Prueba el manejo de errores al inicializar chains"""
        llm_service_prod._force_chain_error = True
        with pytest.raises(Exception, match="Error al crear las cadenas de procesamiento"):
            llm_service_prod._initialize_chains()

    @pytest.mark.asyncio
    async def test_process_resumen_error(self, llm_service):
        """Prueba el manejo de errores en process_resumen"""
        # Configurar el mock para lanzar una excepción
        llm_service.chain_0.ainvoke.side_effect = Exception("Error de procesamiento")
        
        with pytest.raises(Exception, match="Error de procesamiento"):
            await llm_service.process_resumen("test")

    @pytest.mark.asyncio
    async def test_process_unification_error(self, llm_service):
        """Prueba el manejo de errores en process_unification"""
        # Configurar el mock para lanzar una excepción
        llm_service.chain_1.ainvoke.side_effect = Exception("Error de procesamiento")
        
        with pytest.raises(Exception, match="Error de procesamiento"):
            await llm_service.process_unification("test")

    @pytest.mark.asyncio
    async def test_process_chatbot_query_error(self, llm_service):
        """Prueba el manejo de errores en process_chatbot_query"""
        # Configurar el mock para chain_2
        llm_service.chain_2.ainvoke.side_effect = Exception("Error de procesamiento")
        
        # Configurar el mock para llm_2 como fallback
        llm_service.llm_2 = AsyncMock()
        llm_service.llm_2.agenerate.side_effect = Exception("Error de procesamiento")
        
        with pytest.raises(Exception, match="Error de procesamiento"):
            await llm_service.process_chatbot_query("test", "test docs")

    def test_initialize_without_validation(self):
        """Test inicialización sin validación de API key"""
        service = LLMService(testing=False, validate_on_init=False)
        assert service is not None
        assert not service.testing
        assert not service.validate_on_init

    def test_initialize_with_custom_settings(self):
        """Test inicialización con configuración personalizada"""
        settings = Settings(
            OPENAI_API_KEY="sk-test-mock-key-123456789",
            OPENAI_MODEL="test-model",
            OPENAI_TEMPERATURE=0.5,
            USERNAME="test_user",
            PASSWORD="test_pass",
            EMPRESA_ID=1,
            PORT=5000,
            DEBUG=False,
            TESTING=True  # Aseguramos que esté en modo testing
        )
        service = LLMService(testing=True, settings=settings)
        assert service.settings.OPENAI_API_KEY.startswith("sk-")  # Verificamos que comience con sk-
        assert service.settings.OPENAI_MODEL == "test-model"
        assert service.settings.OPENAI_TEMPERATURE == 0.5

    @patch('os.environ')
    def test_initialize_models_env_config(self, mock_env):
        """Test configuración del entorno en initialize_models"""
        # Crear servicio en modo testing para evitar inicialización real
        service = LLMService(testing=True)
        
        # Verificar que en modo testing no se configura el entorno
        mock_env.get.assert_not_called()
        
        # Verificar que los chains se inicializaron como AsyncMock
        assert isinstance(service.chain_0, AsyncMock)
        assert isinstance(service.chain_1, AsyncMock)
        assert isinstance(service.chain_2, AsyncMock)

    def test_initialize_chains_no_llm(self):
        """Test inicialización de chains sin LLM configurado"""
        service = LLMService(testing=False, validate_on_init=False)
        service._initialize_chains()
        
        # En modo no testing, verificamos que los chains se crean como cadenas de Runnable
        # y que tienen la estructura correcta
        assert service.chain_0 is not None
        assert service.chain_1 is not None
        assert service.chain_2 is not None
        
        # Verificar que los prompts están configurados
        assert hasattr(service, 'prompt_template_0')
        assert hasattr(service, 'prompt_template_1')
        assert hasattr(service, 'prompt_template_2')
        
        # Verificar que los chains tienen los componentes necesarios
        assert 'input_text' in service.prompt_template_0.input_variables
        assert 'resumen_ia' in service.prompt_template_1.input_variables
        assert all(var in service.prompt_template_2.input_variables for var in ['documentos', 'pregunta'])

    @pytest.mark.asyncio
    async def test_process_resumen_long_input(self, llm_service):
        """Test procesamiento de resumen con texto largo"""
        long_text = "x" * 10000
        result = await llm_service.process_resumen(long_text)
        assert result == "Test resumen"
        assert llm_service.chain_0.ainvoke.called

    @pytest.mark.asyncio
    async def test_process_unification_long_input(self, llm_service):
        """Test unificación con texto largo"""
        long_text = "x" * 10000
        result = await llm_service.process_unification(long_text)
        assert result == '{"respuestaIA":[{"resumen":"Test resumen"}]}'
        assert llm_service.chain_1.ainvoke.called

    def test_prompt_templates_initialization(self, llm_service):
        """Test inicialización de templates de prompts"""
        assert hasattr(llm_service, 'prompt_template_0')
        assert hasattr(llm_service, 'prompt_template_1')
        assert hasattr(llm_service, 'prompt_template_2')
        assert "input_text" in llm_service.prompt_template_0.input_variables
        assert "resumen_ia" in llm_service.prompt_template_1.input_variables
        assert "documentos" in llm_service.prompt_template_2.input_variables
        assert "pregunta" in llm_service.prompt_template_2.input_variables

    def test_inicializacion_testing(self, mock_settings):
        """Test de inicialización en modo testing"""
        service = LLMService(testing=True, settings=mock_settings)
        assert service.testing == True
        assert service.settings == mock_settings
        assert hasattr(service, 'prompt_template_0')
        assert hasattr(service, 'prompt_template_1')
        assert hasattr(service, 'prompt_template_2')

    def test_inicializacion_produccion(self, mock_settings):
        """Test de inicialización en modo producción"""
        service = LLMService(testing=False, settings=mock_settings, validate_on_init=True)
        assert service.testing == False
        assert service.settings == mock_settings
        assert os.environ.get("OPENAI_API_KEY") == mock_settings.OPENAI_API_KEY

    def test_validacion_api_key_invalida(self, mock_settings):
        """Test de validación con API key inválida"""
        mock_settings.OPENAI_API_KEY = "invalid_key"
        with pytest.raises(ValueError, match="Error al validar credenciales"):
            LLMService(testing=False, settings=mock_settings)

    def test_validacion_api_key_vacia(self, mock_settings):
        """Test de validación con API key vacía"""
        mock_settings.OPENAI_API_KEY = ""
        with pytest.raises(ValueError, match="OPENAI_API_KEY no está configurada"):
            LLMService(testing=False, settings=mock_settings)

    def test_validacion_modelo_no_configurado(self, mock_settings):
        """Test de validación cuando el modelo no está configurado"""
        mock_settings.OPENAI_MODEL = None
        with pytest.raises(ValueError, match="OPENAI_MODEL no está configurado"):
            LLMService(testing=False, settings=mock_settings)

    @pytest.mark.asyncio
    async def test_process_resumen(self, mock_settings):
        """Test de procesamiento de resumen"""
        service = LLMService(testing=True, settings=mock_settings)
        service.chain_0 = AsyncMock()
        service.chain_0.ainvoke.return_value = "Resumen procesado"
        
        resultado = await service.process_resumen("Texto de prueba")
        assert resultado == "Resumen procesado"
        service.chain_0.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_unification(self, mock_settings):
        """Test de unificación de resúmenes"""
        service = LLMService(testing=True, settings=mock_settings)
        service.chain_1 = AsyncMock()
        service.chain_1.ainvoke.return_value = '{"resumen": "unificado"}'
        
        resultado = await service.process_unification("Resumen 1. Resumen 2.")
        assert resultado == '{"resumen": "unificado"}'
        service.chain_1.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_chatbot_query(self, mock_settings):
        """Test de procesamiento de consulta del chatbot"""
        service = LLMService(testing=True, settings=mock_settings)
        service.chain_2 = AsyncMock()
        service.chain_2.ainvoke.return_value = "Respuesta del chatbot"
        
        resultado = await service.process_chatbot_query("¿Pregunta?", "Documentos de contexto")
        assert resultado == "Respuesta del chatbot"
        service.chain_2.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_chatbot_query_sin_documentos(self, mock_settings):
        """Test de procesamiento de consulta sin documentos"""
        service = LLMService(testing=True, settings=mock_settings)
        
        resultado = await service.process_chatbot_query("¿Pregunta?", "")
        assert resultado == "No existen datos dentro de los documentos de la licitación."

    @pytest.mark.asyncio
    async def test_process_chatbot_query_error_chain(self, mock_settings):
        """Test de procesamiento de consulta cuando falla el chain principal"""
        service = LLMService(testing=True, settings=mock_settings)
        service.chain_2 = AsyncMock()
        service.chain_2.ainvoke.side_effect = Exception("Error en chain")
        service.llm_2 = AsyncMock()
        service.llm_2.agenerate.return_value = MagicMock(generations=[
            [MagicMock(text="Respuesta fallback")]
        ])
        
        resultado = await service.process_chatbot_query("¿Pregunta?", "Documentos")
        assert resultado == "Respuesta fallback"

    def test_get_api_key_info_testing(self, mock_settings):
        """Test de obtención de información de API key en modo testing"""
        service = LLMService(testing=True, settings=mock_settings)
        info = service.get_api_key_info()
        assert info["status"] == "success"
        assert info["is_valid"] == True

    def test_get_api_key_info_sin_key(self, mock_settings):
        """Test de obtención de información cuando no hay API key"""
        mock_settings.OPENAI_API_KEY = None
        service = LLMService(testing=False, settings=mock_settings, validate_on_init=False)
        info = service.get_api_key_info()
        assert info["status"] == "error"
        assert info["is_valid"] == False
        assert info["message"] == "API key no configurada"

    def test_refresh_api_key_testing(self, mock_settings):
        """Test de refresh de API key en modo testing"""
        service = LLMService(testing=True, settings=mock_settings)
        service.refresh_api_key()  # No debería lanzar excepciones

    def test_refresh_api_key_produccion(self, mock_settings):
        """Test de refresh de API key en modo producción"""
        # Configurar una API key de prueba genérica
        test_api_key = "sk-test-mock-key-123456789"
        
        # Configurar el mock para devolver siempre la API key de prueba
        mock_settings.OPENAI_API_KEY = test_api_key
        mock_settings.get_settings.return_value = mock_settings
        
        # Establecer la API key en el entorno
        os.environ["OPENAI_API_KEY"] = test_api_key

        service = LLMService(testing=False, settings=mock_settings, validate_on_init=True)
        
        # Ejecutar el refresh
        service.refresh_api_key()

        # Verificar que la API key no ha cambiado
        assert os.environ.get("OPENAI_API_KEY") == test_api_key
        assert service.settings.OPENAI_API_KEY == test_api_key

    def test_refresh_api_key_error(self, mock_settings):
        """Test de refresh de API key cuando hay error"""
        mock_settings.OPENAI_API_KEY = None
        service = LLMService(testing=False, settings=mock_settings, validate_on_init=False)
        
        # Forzar la validación de la API key antes de refrescar
        with patch.object(service, '_validate_api_key', side_effect=ValueError("OPENAI_API_KEY no está configurada")):
            with pytest.raises(ValueError, match="OPENAI_API_KEY no está configurada"):
                service.refresh_api_key() 