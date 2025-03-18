import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.licitacion_service import LicitacionService
from src.services.llm_service import LLMService
from datetime import datetime
import json

@pytest.fixture
def llm_service():
    """Fixture que proporciona un mock del servicio LLM"""
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.process_resumen = AsyncMock()
    mock_llm.process_unification = AsyncMock()
    mock_llm.process_chatbot_query = AsyncMock()
    return mock_llm

@pytest.fixture
def mock_repository():
    """Fixture que proporciona un mock del repositorio"""
    mock_repo = MagicMock()
    mock_repo.obtener_documentos_procesados = AsyncMock()
    mock_repo.obtener_contenido_documento = AsyncMock()
    mock_repo.obtener_respuesta_ia = AsyncMock()
    mock_repo.guardar_respuesta_ia = AsyncMock()
    return mock_repo

@pytest.fixture
def licitacion_service(llm_service, mock_repository):
    """Fixture que proporciona una instancia del servicio de licitaciones"""
    service = LicitacionService(llm_service, testing=True)
    service.repository = mock_repository
    return service

@pytest.mark.unit
class TestLicitacionService:
    """Tests unitarios para el servicio de licitaciones"""
    
    def test_inicializacion(self, licitacion_service, mock_repository):
        """Test para verificar la inicialización correcta del servicio"""
        assert licitacion_service.llm_service is not None
        assert licitacion_service.repository == mock_repository
        assert licitacion_service.tokenizer is not None
    
    @pytest.mark.asyncio
    async def test_procesar_licitaciones_todas(self, licitacion_service, mock_repository):
        """Test para procesar todas las licitaciones"""
        # Mock de documentos procesados
        mock_docs = {
            "123": ["doc1.pdf", "doc2.pdf"],
            "456": ["doc3.pdf"]
        }
        mock_repository.obtener_documentos_procesados.return_value = mock_docs
        
        # Mock de contenido de documentos
        mock_repository.obtener_contenido_documento.return_value = "Contenido de prueba"
        
        # Mock de respuestas IA
        mock_repository.obtener_respuesta_ia.return_value = None
        mock_repository.guardar_respuesta_ia.return_value = True
        
        # Mock de respuestas LLM
        licitacion_service.llm_service.process_resumen.return_value = "Resumen de prueba"
        licitacion_service.llm_service.process_unification.return_value = '{"resumen": "unificado"}'
        
        # Ejecutar el método
        resultado = await licitacion_service.procesar_licitaciones()
        
        # Verificaciones
        assert resultado["total_procesadas"] == 2
        assert resultado["exitosas"] == 2
        assert resultado["existentes"] == 0
        assert resultado["con_error"] == 0
        assert len(resultado["resultados"]) == 2
    
    @pytest.mark.asyncio
    async def test_procesar_licitaciones_especificas(self, licitacion_service, mock_repository):
        """Test para procesar licitaciones específicas"""
        # Mock de documentos procesados
        mock_docs = {
            "123": ["doc1.pdf"],
            "456": ["doc2.pdf"]
        }
        mock_repository.obtener_documentos_procesados.return_value = mock_docs
        
        # Mock de contenido de documentos
        mock_repository.obtener_contenido_documento.return_value = "Contenido de prueba"
        
        # Mock de respuestas IA
        mock_repository.obtener_respuesta_ia.return_value = None
        mock_repository.guardar_respuesta_ia.return_value = True
        
        # Mock de respuestas LLM
        licitacion_service.llm_service.process_resumen.return_value = "Resumen de prueba"
        licitacion_service.llm_service.process_unification.return_value = '{"resumen": "unificado"}'
        
        # Ejecutar el método con códigos específicos
        resultado = await licitacion_service.procesar_licitaciones(["123"])
        
        # Verificaciones
        assert resultado["total_procesadas"] == 1
        assert resultado["exitosas"] == 1
        assert resultado["existentes"] == 0
        assert resultado["con_error"] == 0
        assert len(resultado["resultados"]) == 1
        assert resultado["resultados"][0]["codigo_licitacion"] == "123"
    
    @pytest.mark.asyncio
    async def test_procesar_consulta_chatbot(self, licitacion_service, mock_repository):
        """Test para procesar consulta del chatbot"""
        # Mock de documentos procesados
        mock_docs = {
            "123": ["doc1.pdf"]
        }
        mock_repository.obtener_documentos_procesados.return_value = mock_docs
        
        # Mock de contenido de documentos
        mock_repository.obtener_contenido_documento.return_value = "Contenido de prueba"
        
        # Mock de respuesta del chatbot
        licitacion_service.llm_service.process_chatbot_query.return_value = "Respuesta del chatbot"
        
        # Ejecutar el método
        resultado = await licitacion_service.procesar_consulta_chatbot("123", "pregunta de prueba")
        
        # Verificaciones
        assert resultado == "Respuesta del chatbot"
        mock_repository.obtener_documentos_procesados.assert_called_once()
        mock_repository.obtener_contenido_documento.assert_called_once()
        licitacion_service.llm_service.process_chatbot_query.assert_called_once()
    
    def test_dividir_texto(self, licitacion_service):
        """Test para dividir texto en fragmentos"""
        texto = "a" * 150000
        tamano_fragmento = 100000
        
        fragmentos = licitacion_service.dividir_texto(texto, tamano_fragmento)
        
        assert len(fragmentos) == 2
        assert len(fragmentos[0]) == tamano_fragmento
        assert len(fragmentos[1]) == 50000
    
    def test_limpiar_y_convertir_json(self, licitacion_service):
        """Test para limpiar y convertir respuesta a JSON"""
        entrada = '```json\n{"key": "value"}\n```'
        resultado = licitacion_service._limpiar_y_convertir_json(entrada)
        
        assert resultado == '{"key": "value"}'
    
    @pytest.mark.asyncio
    async def test_obtener_documentos(self, licitacion_service, mock_repository):
        """Test para obtener documentos de una licitación"""
        # Mock de documentos
        mock_docs = {
            "123": ["doc1.pdf", "doc2.pdf"]
        }
        
        # Mock de contenido
        mock_repository.obtener_contenido_documento.return_value = "Contenido de prueba"
        
        # Ejecutar el método
        resultado = await licitacion_service.obtener_documentos("123", mock_docs)
        
        # Verificaciones
        assert "Contenido de prueba" in resultado
        assert "DOCUMENTO 1" in resultado
        assert "DOCUMENTO 2" in resultado
        assert mock_repository.obtener_contenido_documento.call_count == 2 

    @pytest.mark.asyncio
    async def test_procesar_licitaciones_error_documentos(self, licitacion_service, mock_repository):
        """Test para procesar licitaciones cuando hay error al obtener documentos"""
        # Mock de error al obtener documentos
        error_msg = "Error al obtener documentos"
        mock_repository.obtener_documentos_procesados.side_effect = Exception(error_msg)
        
        try:
            # Ejecutar el método
            resultado = await licitacion_service.procesar_licitaciones()
            
            # Verificaciones
            assert resultado["total_procesadas"] == 0
            assert resultado["exitosas"] == 0
            assert resultado["con_error"] == 0
            assert len(resultado["resultados"]) == 0
            assert error_msg in resultado["error"]
            
        except Exception as e:
            # Si la excepción no es manejada por el servicio, verificar que sea la correcta
            assert str(e) == error_msg

    @pytest.mark.asyncio
    async def test_procesar_licitaciones_respuesta_existente(self, licitacion_service, mock_repository):
        """Test para procesar licitaciones cuando ya existe respuesta"""
        # Mock de documentos procesados
        mock_docs = {
            "123": ["doc1.pdf"]
        }
        mock_repository.obtener_documentos_procesados.return_value = mock_docs
        
        # Mock de respuesta IA existente
        mock_repository.obtener_respuesta_ia.return_value = '{"resumen": "existente"}'
        
        # Ejecutar el método
        resultado = await licitacion_service.procesar_licitaciones()
        
        # Verificaciones
        assert resultado["total_procesadas"] == 1
        assert resultado["exitosas"] == 0
        assert resultado["existentes"] == 1
        assert resultado["con_error"] == 0
        assert len(resultado["resultados"]) == 1

    @pytest.mark.asyncio
    async def test_procesar_licitaciones_error_contenido(self, licitacion_service, mock_repository):
        """Test para procesar licitaciones cuando hay error al obtener contenido"""
        # Mock de documentos procesados
        mock_docs = {
            "123": ["doc1.pdf"]
        }
        mock_repository.obtener_documentos_procesados.return_value = mock_docs
        
        # Mock de error al obtener contenido
        mock_repository.obtener_contenido_documento.side_effect = Exception("Error al obtener contenido")
        mock_repository.obtener_respuesta_ia.return_value = None
        
        # Ejecutar el método
        resultado = await licitacion_service.procesar_licitaciones()
        
        # Verificaciones
        assert resultado["total_procesadas"] == 1
        assert resultado["exitosas"] == 0
        assert resultado["existentes"] == 0
        assert resultado["con_error"] == 1
        assert len(resultado["resultados"]) == 1
        assert resultado["resultados"][0]["error"] == "No se pudo obtener contenido de ningún documento"

    @pytest.mark.asyncio
    async def test_procesar_consulta_chatbot_sin_documentos(self, licitacion_service, mock_repository):
        """Test para procesar consulta cuando no hay documentos"""
        # Mock de documentos vacíos
        mock_repository.obtener_documentos_procesados.return_value = {}
        
        # Ejecutar el método
        resultado = await licitacion_service.procesar_consulta_chatbot("123", "pregunta")
        
        # Verificaciones
        assert resultado == "No se encontraron documentos para la licitación."
        mock_repository.obtener_contenido_documento.assert_not_called()
        licitacion_service.llm_service.process_chatbot_query.assert_not_called()

    @pytest.mark.asyncio
    async def test_procesar_consulta_chatbot_error_contenido(self, licitacion_service, mock_repository):
        """Test para procesar consulta cuando hay error al obtener contenido"""
        # Mock de documentos
        mock_docs = {
            "123": ["doc1.pdf"]
        }
        mock_repository.obtener_documentos_procesados.return_value = mock_docs
        
        # Mock de error al obtener contenido
        mock_repository.obtener_contenido_documento.side_effect = Exception("Error al obtener contenido")
        
        # Ejecutar el método
        resultado = await licitacion_service.procesar_consulta_chatbot("123", "pregunta")
        
        # Verificar que se retorna el mensaje de error esperado
        assert resultado == "No se pudo obtener contenido de ningún documento"
        mock_repository.obtener_contenido_documento.assert_called_once()
        licitacion_service.llm_service.process_chatbot_query.assert_not_called()

    def test_dividir_texto_vacio(self, licitacion_service):
        """Test para dividir texto vacío"""
        texto = ""
        fragmentos = licitacion_service.dividir_texto(texto, 1000)
        assert len(fragmentos) == 0  # El método retorna una lista vacía para un texto vacío

    def test_dividir_texto_menor_que_tamano(self, licitacion_service):
        """Test para dividir texto menor que el tamaño máximo"""
        texto = "texto corto"
        tamano_fragmento = 1000
        fragmentos = licitacion_service.dividir_texto(texto, tamano_fragmento)
        assert len(fragmentos) == 1
        assert fragmentos[0] == texto

    def test_limpiar_y_convertir_json_invalido(self, licitacion_service):
        """Test para limpiar y convertir JSON inválido"""
        entrada = 'no es json'
        try:
            resultado = licitacion_service._limpiar_y_convertir_json(entrada)
            # Si no lanza excepción, debe retornar el texto original
            assert resultado == entrada
        except json.JSONDecodeError:
            # Si lanza excepción, es un comportamiento aceptable
            pass
        except Exception as e:
            # Cualquier otra excepción no es aceptable
            pytest.fail(f"Se lanzó una excepción inesperada: {str(e)}")

    def test_limpiar_y_convertir_json_sin_markdown(self, licitacion_service):
        """Test para limpiar y convertir JSON sin marcadores markdown"""
        entrada = '{"key": "value"}'
        resultado = licitacion_service._limpiar_y_convertir_json(entrada)
        assert resultado == entrada

    @pytest.mark.asyncio
    async def test_obtener_documentos_vacios(self, licitacion_service, mock_repository):
        """Test para obtener documentos cuando no hay documentos"""
        mock_docs = {}
        with pytest.raises(ValueError, match="No se encontraron documentos"):
            await licitacion_service.obtener_documentos("123", mock_docs)

    @pytest.mark.asyncio
    async def test_obtener_documentos_error_contenido(self, licitacion_service, mock_repository):
        """Test para obtener documentos cuando hay error al obtener contenido"""
        mock_docs = {
            "123": ["doc1.pdf"]
        }
        mock_repository.obtener_contenido_documento.side_effect = Exception("Error al obtener contenido")
        
        with pytest.raises(ValueError, match="No se pudo obtener contenido de ningún documento"):
            await licitacion_service.obtener_documentos("123", mock_docs)

    @pytest.mark.asyncio
    async def test_procesar_licitacion_respuesta_existente(self, licitacion_service, mock_repository):
        """Test para procesar una licitación con respuesta existente"""
        codigo_licitacion = "123"
        respuesta_existente = '{"resumen": "existente"}'
        mock_repository.obtener_respuesta_ia.return_value = respuesta_existente
        
        resultado = await licitacion_service.procesar_licitacion(codigo_licitacion)
        assert resultado == respuesta_existente
        mock_repository.obtener_documentos_procesados.assert_not_called()

    @pytest.mark.asyncio
    async def test_procesar_licitacion_sin_documentos(self, licitacion_service, mock_repository):
        """Test para procesar una licitación sin documentos"""
        codigo_licitacion = "123"
        mock_repository.obtener_respuesta_ia.return_value = None
        mock_repository.obtener_documentos_procesados.return_value = {}
        
        with pytest.raises(ValueError, match=f"No se encontraron documentos para la licitación {codigo_licitacion}"):
            await licitacion_service.procesar_licitacion(codigo_licitacion)

    @pytest.mark.asyncio
    async def test_procesar_licitacion_error_api_key(self, licitacion_service, mock_repository):
        """Test para procesar una licitación con error de API key"""
        codigo_licitacion = "123"
        mock_repository.obtener_respuesta_ia.return_value = None
        mock_repository.obtener_documentos_procesados.return_value = {"123": ["doc1.pdf"]}
        mock_repository.obtener_contenido_documento.return_value = "Contenido de prueba"
        
        # Configurar el mock para retornar valores apropiados
        mock_resumen = AsyncMock()
        mock_resumen.side_effect = [
            Exception("invalid_api_key"),  # Primer intento falla
            "Resumen exitoso"  # Segundo intento exitoso
        ]
        licitacion_service.llm_service.process_resumen = mock_resumen
        
        # Configurar el mock de unificación para retornar un JSON válido
        mock_unification = AsyncMock()
        mock_unification.return_value = '{"resumen": "unificado"}'
        licitacion_service.llm_service.process_unification = mock_unification
        
        # Configurar el mock de refresh_api_key
        licitacion_service.llm_service.refresh_api_key = MagicMock()
        
        # Ejecutar el método
        resultado = await licitacion_service.procesar_licitacion(codigo_licitacion)
        
        # Verificaciones
        assert resultado["codigo_licitacion"] == codigo_licitacion
        assert "resultado_analisis" in resultado
        assert json.loads(resultado["resultado_analisis"])["resumen"] == "unificado"
        
        # Verificar que se llamaron los métodos esperados
        assert mock_resumen.call_count == 2  # Se llamó dos veces debido al reintento
        assert mock_unification.call_count == 1  # Se llamó una vez con el resumen exitoso
        assert licitacion_service.llm_service.refresh_api_key.call_count == 1  # Se llamó una vez para refrescar la key

    @pytest.mark.asyncio
    async def test_procesar_licitacion_error_guardado(self, licitacion_service, mock_repository):
        """Test para procesar una licitación con error al guardar"""
        codigo_licitacion = "123"
        mock_repository.obtener_respuesta_ia.return_value = None
        mock_repository.obtener_documentos_procesados.return_value = {"123": ["doc1.pdf"]}
        mock_repository.obtener_contenido_documento.return_value = "Contenido de prueba"
        mock_repository.guardar_respuesta_ia.return_value = False
        
        licitacion_service.llm_service.process_resumen.return_value = "Resumen de prueba"
        licitacion_service.llm_service.process_unification.return_value = '{"resumen": "unificado"}'
        
        with pytest.raises(ValueError, match=f"Error al almacenar datos para la licitación {codigo_licitacion}"):
            await licitacion_service.procesar_licitacion(codigo_licitacion)

    def test_dividir_texto_error(self, licitacion_service):
        """Test para dividir texto con error"""
        texto = None  # Esto debería causar un error
        with pytest.raises(Exception):
            licitacion_service.dividir_texto(texto)

    @pytest.mark.asyncio
    async def test_procesar_licitacion_error_unificacion(self, licitacion_service, mock_repository):
        """Test para procesar una licitación con error en la unificación"""
        codigo_licitacion = "123"
        mock_repository.obtener_respuesta_ia.return_value = None
        mock_repository.obtener_documentos_procesados.return_value = {"123": ["doc1.pdf"]}
        mock_repository.obtener_contenido_documento.return_value = "Contenido de prueba"
        
        licitacion_service.llm_service.process_resumen.return_value = "Resumen de prueba"
        licitacion_service.llm_service.process_unification.side_effect = Exception("Error en unificación")
        
        with pytest.raises(Exception, match="Error en unificación"):
            await licitacion_service.procesar_licitacion(codigo_licitacion)

    @pytest.mark.asyncio
    async def test_obtener_documentos_contenido_vacio(self, licitacion_service, mock_repository):
        """Test para obtener documentos cuando el contenido está vacío"""
        mock_docs = {
            "123": ["doc1.pdf"]
        }
        mock_repository.obtener_contenido_documento.return_value = "   "  # Contenido vacío
        
        with pytest.raises(ValueError, match="No se pudo obtener contenido de ningún documento"):
            await licitacion_service.obtener_documentos("123", mock_docs)

    def test_limpiar_y_convertir_json_error_inesperado(self, licitacion_service):
        """Test para limpiar y convertir JSON con error inesperado"""
        entrada = None  # Esto debería causar un error que no sea JSONDecodeError
        with pytest.raises(Exception):
            licitacion_service._limpiar_y_convertir_json(entrada)

    @pytest.mark.asyncio
    async def test_procesar_licitacion_contenido_vacio(self, licitacion_service, mock_repository):
        """Test para procesar una licitación cuando el contenido está vacío"""
        codigo_licitacion = "123"
        mock_repository.obtener_respuesta_ia.return_value = None
        mock_repository.obtener_documentos_procesados.return_value = {"123": ["doc1.pdf"]}
        mock_repository.obtener_contenido_documento.return_value = "   "
        
        with pytest.raises(ValueError, match="No se pudo obtener contenido de ningún documento"):
            await licitacion_service.procesar_licitacion(codigo_licitacion)

    @pytest.mark.asyncio
    async def test_procesar_licitacion_error_refresh_api_key(self, licitacion_service, mock_repository):
        """Test para procesar una licitación cuando falla el refresh de API key"""
        codigo_licitacion = "123"
        mock_repository.obtener_respuesta_ia.return_value = None
        mock_repository.obtener_documentos_procesados.return_value = {"123": ["doc1.pdf"]}
        mock_repository.obtener_contenido_documento.return_value = "Contenido de prueba"
        
        # Configurar el error de API key y el error en el refresh
        licitacion_service.llm_service.process_resumen.side_effect = Exception("invalid_api_key")
        licitacion_service.llm_service.refresh_api_key.side_effect = Exception("Error refrescando API key")
        
        with pytest.raises(ValueError, match="Error de autenticación persistente"):
            await licitacion_service.procesar_licitacion(codigo_licitacion)

    @pytest.mark.asyncio
    async def test_procesar_licitacion_multiples_fragmentos(self, licitacion_service, mock_repository):
        """Test para procesar una licitación con múltiples fragmentos de texto"""
        codigo_licitacion = "123"
        mock_repository.obtener_respuesta_ia.return_value = None
        mock_repository.obtener_documentos_procesados.return_value = {"123": ["doc1.pdf"]}
        mock_repository.obtener_contenido_documento.return_value = "a" * 150000  # Texto largo que generará múltiples fragmentos
        mock_repository.guardar_respuesta_ia.return_value = True
        
        # Mock de respuestas para cada fragmento
        licitacion_service.llm_service.process_resumen.side_effect = [
            "Resumen fragmento 1",
            "Resumen fragmento 2"
        ]
        licitacion_service.llm_service.process_unification.return_value = '{"resumen": "unificado"}'
        
        resultado = await licitacion_service.procesar_licitacion(codigo_licitacion)
        
        assert resultado["codigo_licitacion"] == codigo_licitacion
        assert "resultado_analisis" in resultado
        assert licitacion_service.llm_service.process_resumen.call_count == 2

    @pytest.mark.asyncio
    async def test_procesar_licitacion_error_procesamiento_fragmento(self, licitacion_service, mock_repository):
        """Test para procesar una licitación cuando falla el procesamiento de un fragmento"""
        codigo_licitacion = "123"
        mock_repository.obtener_respuesta_ia.return_value = None
        mock_repository.obtener_documentos_procesados.return_value = {"123": ["doc1.pdf"]}
        mock_repository.obtener_contenido_documento.return_value = "a" * 150000
        
        # Configurar el mock para que falle en todos los intentos
        mock_resumen = AsyncMock()
        mock_resumen.side_effect = Exception("Error procesando fragmento")
        licitacion_service.llm_service.process_resumen = mock_resumen
        
        # No necesitamos configurar process_unification ya que nunca se llegará a llamar
        
        with pytest.raises(ValueError, match="No se pudo procesar ningún fragmento"):
            await licitacion_service.procesar_licitacion(codigo_licitacion)
        
        # Verificar que se intentó procesar al menos una vez
        assert mock_resumen.call_count >= 1

    @pytest.mark.asyncio
    async def test_procesar_consulta_chatbot_error_query(self, licitacion_service, mock_repository):
        """Test para procesar consulta cuando falla el proceso de query"""
        mock_docs = {
            "123": ["doc1.pdf"]
        }
        mock_repository.obtener_documentos_procesados.return_value = mock_docs
        mock_repository.obtener_contenido_documento.return_value = "Contenido de prueba"
        
        # Configurar el mock para que lance la excepción
        mock_query = AsyncMock()
        mock_query.side_effect = Exception("Error en query")
        licitacion_service.llm_service.process_chatbot_query = mock_query
        
        resultado = await licitacion_service.procesar_consulta_chatbot("123", "pregunta")
        assert resultado == "Error al procesar la consulta con el modelo de lenguaje."

    def test_dividir_texto_tamano_cero(self, licitacion_service):
        """Test para dividir texto con tamaño de fragmento cero"""
        texto = "texto de prueba"
        with pytest.raises(ValueError, match="range\\(\\) arg 3 must not be zero"):
            licitacion_service.dividir_texto(texto, 0)

    def test_dividir_texto_tamano_negativo(self, licitacion_service):
        """Test para dividir texto con tamaño de fragmento negativo"""
        texto = "texto de prueba"
        fragmentos = licitacion_service.dividir_texto(texto, -1000)
        assert len(fragmentos) == 0  # El método retorna una lista vacía para tamaños negativos

    @pytest.mark.asyncio
    async def test_procesar_licitaciones_codigo_invalido(self, licitacion_service, mock_repository):
        """Test para procesar licitaciones con código inválido"""
        mock_docs = {
            "123": ["doc1.pdf"]
        }
        mock_repository.obtener_documentos_procesados.return_value = mock_docs
        
        try:
            # Intentar procesar un código que no existe
            resultado = await licitacion_service.procesar_licitaciones(["456"])
            
            # Verificaciones
            assert resultado["total_procesadas"] == 1
            assert resultado["exitosas"] == 0
            assert resultado["existentes"] == 0
            assert resultado["con_error"] == 1
            assert len(resultado["resultados"]) == 1
            assert "error" in resultado["resultados"][0]
            assert "No se encontraron las licitaciones especificadas" in resultado["error"]
            
        except ValueError as e:
            # Si la excepción no es manejada por el servicio, verificar que sea la correcta
            assert str(e) == "No se encontraron las licitaciones especificadas"

    @pytest.mark.asyncio
    async def test_procesar_licitaciones_sin_codigos(self, licitacion_service, mock_repository):
        """Test para procesar licitaciones sin proporcionar códigos"""
        mock_repository.obtener_documentos_procesados.return_value = {}
        
        with pytest.raises(ValueError, match="No se encontraron licitaciones para procesar"):
            await licitacion_service.procesar_licitaciones([]) 