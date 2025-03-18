from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from core.config import get_settings
from core.logging import get_logger
from unittest.mock import AsyncMock
import os

logger = get_logger(__name__)

class LLMService:
    def __init__(self, testing=False, settings=None, validate_on_init=True):
        """
        Inicializa el servicio LLM.
        Args:
            testing (bool): Si es True, se ejecuta en modo testing.
            settings (Settings): Configuración personalizada. Si es None, se usa la configuración por defecto.
            validate_on_init (bool): Si es True, valida la API key al inicializar.
        """
        self.testing = testing
        self.settings = settings or get_settings()
        self.validate_on_init = validate_on_init
        
        if not testing and validate_on_init:
            self._validate_api_key()
            self._initialize_models()
        self._initialize_prompts()
        self._initialize_chains()
        
    def _validate_api_key(self):
        """Valida que la API key esté configurada correctamente"""
        if self.testing:
            logger.info("Modo testing: Omitiendo validación de API key")
            return
            
        if not self.settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY no está configurada")
            
        api_key = self.settings.OPENAI_API_KEY.strip()
        
        if not api_key.startswith("sk-"):
            logger.error("Error en la validación de credenciales: Formato de API key inválido")
            raise ValueError("Error al validar credenciales")
            
        logger.info("✅ Credenciales validadas correctamente")
        
    def _initialize_models(self):
        """Inicializa los modelos LLM"""
        try:
            api_key = self.settings.OPENAI_API_KEY.strip()
            os.environ["OPENAI_API_KEY"] = api_key
            
            if os.environ.get("OPENAI_API_KEY") != api_key:
                raise ValueError("Error al configurar credenciales en el entorno")
                
            if not self.settings.OPENAI_MODEL:
                raise ValueError("OPENAI_MODEL no está configurado")
            
            self.llm_0 = ChatOpenAI(
                api_key=api_key,
                model=self.settings.OPENAI_MODEL, 
                temperature=self.settings.OPENAI_TEMPERATURE
            )
            self.llm_1 = ChatOpenAI(
                api_key=api_key,
                model=self.settings.OPENAI_MODEL, 
                temperature=self.settings.OPENAI_TEMPERATURE
            )
            self.llm_2 = ChatOpenAI(
                api_key=api_key,
                model=self.settings.OPENAI_MODEL, 
                temperature=self.settings.OPENAI_TEMPERATURE
            )
            logger.info("✅ Modelos LLM configurados exitosamente")
        except Exception as e:
            logger.error("❌ Error en configuración de modelos LLM")
            raise
    
    def _initialize_prompts(self):
        """Inicializa los templates de prompts"""
        try:
            # Simular un error si estamos en modo testing y se ha configurado para fallar
            if hasattr(self, '_force_prompt_error') and self._force_prompt_error:
                raise ValueError("Error al crear el prompt template")

            self.prompt_template_0 = PromptTemplate(
                input_variables=["input_text"],
                template="""Eres un experto en la gestión de toma de decisiones empresariales y en la gestión de proyectos. 
                En esta tarea, se requiere que realices un resumen del siguiente conjunto de documentos pertenecientes al código {input_text}. 
                Además, proporciona la información de los siguientes puntos en el formato indicado: 
                1. Resumen en no más de 200 palabras. 
                2. Requisitos de la empresa: certificaciones necesarias, disponibilidad, y modalidad presencial o no. 
                3. Perfiles divididos en: cargos, conocimientos, experiencia, certificaciones. 
                4. Duración del proyecto. 
                5. Presupuesto. 
                Si algún punto mencionado anteriormente no se especifica explícitamente en los documentos, indícalo como 'No se especifica en estos documentos'. 
                A continuación, el contenido completo: {input_text}"""
            )

            self.prompt_template_1 = PromptTemplate(
                input_variables=["resumen_ia"],
                template="""Relaciona todos los textos entregados y unifica los resumenes y datos entregados para cada campo: {resumen_ia}. 
                Y utiliza el siguiente formato para que este se almacene tal y como esta con la informacion que unificaste: 
                {{"respuestaIA":[{{"resumen":"string","personalRequerido":[{{"personal1":"string"}},{{"personal2":"string"}}],
                "habilidades":[{{"habilidad1":"string"}},{{"habilidad2":"string"}}],"certificaciones":[{{"certificacion1":"string"}},
                {{"certificacion2":"string"}}],"horasRequeridas":"string","tecnologías":[{{"tecnología1":"string"}},
                {{"tecnología2":"string"}}],"requisitosComerciales":[{{"requisito1":"string"}},{{"requisito2":"string"}}]}}]}}"""
            )

            self.prompt_template_2 = PromptTemplate(
                input_variables=["documentos", "pregunta"],
                template="""Eres un asistente experto en análisis de licitaciones públicas. Tu objetivo es proporcionar respuestas precisas y útiles basadas en la documentación proporcionada.

Basándote en los siguientes documentos de licitación:

{documentos}

Por favor, responde la siguiente pregunta de manera detallada y específica:
{pregunta}

Asegúrate de:
1. Basar tu respuesta solo en la información proporcionada en los documentos
2. Citar específicamente las partes relevantes de los documentos, indicando el número de documento
3. Si la información no está disponible en los documentos, indicarlo claramente
4. Estructurar la respuesta de manera clara y concisa
5. Proporcionar ejemplos específicos cuando sea posible"""
            )
            logger.info("✅ Templates de prompts configurados")
        except Exception as e:
            logger.error(f"❌ Error en configuración de prompts: {str(e)}", exc_info=True)
            raise
    
    def _initialize_chains(self):
        """Inicializa las cadenas de procesamiento"""
        try:
            # Simular un error si estamos en modo testing y se ha configurado para fallar
            if hasattr(self, '_force_chain_error') and self._force_chain_error:
                raise Exception("Error al crear las cadenas de procesamiento")

            if self.testing:
                # En modo testing, usar AsyncMock para las cadenas
                self.chain_0 = AsyncMock()
                self.chain_1 = AsyncMock()
                self.chain_2 = AsyncMock()
            else:
                # En modo normal, crear las cadenas de procesamiento
                if not hasattr(self, 'llm_0'):
                    # Si no se han inicializado los modelos LLM, usar AsyncMock
                    self.llm_0 = AsyncMock()
                    self.llm_1 = AsyncMock()
                    self.llm_2 = AsyncMock()
                    
                self.chain_0 = RunnablePassthrough() | self.prompt_template_0 | self.llm_0 | StrOutputParser()
                self.chain_1 = RunnablePassthrough() | self.prompt_template_1 | self.llm_1 | StrOutputParser()
                self.chain_2 = RunnablePassthrough() | self.prompt_template_2 | self.llm_2 | StrOutputParser()
            logger.info("✅ Cadenas de procesamiento creadas exitosamente")
        except Exception as e:
            logger.error(f"❌ Error en configuración de chains: {str(e)}", exc_info=True)
            raise
    
    async def process_resumen(self, input_text: str) -> str:
        """
        Procesa un fragmento de texto para generar un resumen estructurado
        """
        try:
            logger.info("Procesando resumen con el modelo LLM")
            logger.debug(f"Longitud del texto de entrada: {len(input_text)} caracteres")
            
            # Usar el chain configurado para procesar el resumen
            try:
                response = await self.chain_0.ainvoke({"input_text": input_text})
                logger.info("Resumen generado exitosamente usando chain_0")
                return response
            except Exception as chain_error:
                logger.error(f"Error al procesar con chain_0: {str(chain_error)}")
                raise

        except Exception as e:
            logger.error(f"Error en process_resumen: {str(e)}", exc_info=True)
            raise

    async def process_unification(self, resumen_ia: str) -> str:
        """
        Unifica y estructura los resúmenes generados
        """
        try:
            logger.info("Unificando resúmenes con el modelo LLM")
            logger.debug(f"Longitud del texto de entrada: {len(resumen_ia)} caracteres")
            
            # Usar el chain configurado para unificar resúmenes
            try:
                response = await self.chain_1.ainvoke({"resumen_ia": resumen_ia})
                logger.info("Unificación generada exitosamente usando chain_1")
                return response
            except Exception as chain_error:
                logger.error(f"Error al procesar con chain_1: {str(chain_error)}")
                raise

        except Exception as e:
            logger.error(f"Error en process_unification: {str(e)}", exc_info=True)
            raise
    
    async def process_chatbot_query(self, input_text: str, documentos_texto: str = "") -> str:
        """
        Procesa una consulta del chatbot utilizando el modelo LLM
        """
        try:
            logger.info("Procesando consulta con el modelo LLM")
            logger.debug(f"Longitud del texto de entrada: {len(input_text)} caracteres")
            logger.debug(f"Longitud de documentos: {len(documentos_texto)} caracteres")
            
            if not documentos_texto.strip():
                logger.warning("No se proporcionaron documentos para analizar")
                return "No existen datos dentro de los documentos de la licitación."

            # Usar el chain configurado para procesar la consulta
            try:
                # Preparar los datos para el prompt
                datos_prompt = {
                    "documentos": documentos_texto,
                    "pregunta": input_text
                }
                
                # Procesar con el chain
                response = await self.chain_2.ainvoke(datos_prompt)
                logger.info("Respuesta generada exitosamente usando chain")
                logger.debug(f"Longitud de la respuesta: {len(response)} caracteres")
                return response
            except Exception as chain_error:
                logger.error(f"Error al procesar con chain_2: {str(chain_error)}")
                # Fallback: usar el modelo directamente
                logger.info("Intentando procesar directamente con el modelo...")
                
                # Construir el prompt completo
                prompt_completo = self.prompt_template_2.format(**datos_prompt)
                
                # Crear mensajes para el chat
                from langchain_core.messages import SystemMessage, HumanMessage
                messages = [
                    SystemMessage(content="Eres un asistente experto en análisis de licitaciones públicas. Tu objetivo es proporcionar respuestas precisas y útiles basadas en la documentación proporcionada."),
                    HumanMessage(content=prompt_completo)
                ]
                
                # Llamar al modelo directamente
                response = await self.llm_2.agenerate([messages])
                respuesta = response.generations[0][0].text.strip()
                logger.info("Respuesta generada exitosamente usando fallback")
                return respuesta

        except Exception as e:
            logger.error(f"Error en process_chatbot_query: {str(e)}", exc_info=True)
            raise

    def get_api_key_info(self) -> dict:
        """
        Obtiene información sobre el estado de la API key.
        Returns:
            dict: Diccionario con información sobre el estado de la API key.
        """
        if self.testing:
            return {
                "status": "success",
                "message": "Test mode: API key validation skipped",
                "is_valid": True
            }
        
        if not self.settings.OPENAI_API_KEY:
            return {
                "status": "error",
                "message": "API key no configurada",
                "is_valid": False
            }
        
        try:
            self._validate_api_key()
            return {
                "status": "success",
                "message": "API key válida",
                "is_valid": True
            }
        except ValueError as e:
            return {
                "status": "error",
                "message": str(e),
                "is_valid": False
            }

    def refresh_api_key(self) -> None:
        """
        Recarga la API key desde la configuración
        """
        try:
            if self.testing:
                logger.info("Test mode: Skipping API key refresh")
                return
            self.settings = get_settings()
            self._validate_api_key()
            os.environ["OPENAI_API_KEY"] = self.settings.OPENAI_API_KEY
            self._initialize_models()
            logger.info("✅ API key refrescada exitosamente")
        except Exception as e:
            logger.error(f"❌ Error al refrescar API key: {str(e)}")
            raise 