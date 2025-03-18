from datetime import datetime
import json
from typing import List, Dict, Any, Optional
import tiktoken
import time
from core.config import settings
from core.logging import get_logger
from services.llm_service import LLMService
from repositories.mercadopublico_repository import MercadoPublicoRepository
import logging

logger = get_logger(__name__)

class LicitacionService:
    def __init__(self, llm_service: LLMService, testing: bool = False):
        self.settings = settings
        self.llm_service = llm_service
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.repository = MercadoPublicoRepository(testing=testing)
        self.logger = logging.getLogger(__name__)
    
    def dividir_texto(self, texto: str, tamano_fragmento: int = 100000) -> List[str]:
        """
        Divide un texto en fragmentos según el tamaño especificado
        """
        logger.info("=== Iniciando división de texto ===")
        logger.info(f"Tamaño de fragmento configurado: {tamano_fragmento} caracteres")
        start_time = time.time()
        
        try:
            logger.debug(f"Longitud total del texto: {len(texto)} caracteres")
            fragmentos = []
            
            for i in range(0, len(texto), tamano_fragmento):
                fragmento = texto[i:i+tamano_fragmento]
                fragmentos.append(fragmento)
                logger.debug(f"Fragmento {len(fragmentos)} creado: {len(fragmento)} caracteres")
            
            execution_time = time.time() - start_time
            logger.info(f"✅ Texto dividido en {len(fragmentos)} fragmentos")
            logger.info(f"Tiempo de ejecución: {execution_time:.2f} segundos")
            
            return fragmentos
        except Exception as e:
            logger.error(f"❌ Error al dividir texto: {str(e)}", exc_info=True)
            raise
    
    async def procesar_licitacion(self, codigo_licitacion: str) -> Dict:
        """
        Procesa una licitación específica
        """
        try:
            # Verificar si ya existe un resumen
            respuesta_existente = await self.repository.obtener_respuesta_ia(codigo_licitacion)
            if respuesta_existente:
                logger.info(f"Resumen existente para licitación: {codigo_licitacion}")
                return respuesta_existente

            # Obtener listas agrupadas y documentos
            listas_agrupadas = await self.repository.obtener_documentos_procesados()
            if not listas_agrupadas:
                raise ValueError(f"No se encontraron documentos para la licitación {codigo_licitacion}")

            documentos_texto = await self.obtener_documentos(codigo_licitacion, listas_agrupadas)
            if not documentos_texto.strip():
                raise ValueError(f"No se pudo obtener contenido de los documentos para la licitación {codigo_licitacion}")

            # Dividir texto en fragmentos y procesar con LLM
            fragmentos = self.dividir_texto(documentos_texto)
            respuestas_ia = []
            
            for idx, fragmento in enumerate(fragmentos, 1):
                try:
                    logger.info(f"Procesando fragmento {idx}/{len(fragmentos)}")
                    respuesta = await self.llm_service.process_resumen(fragmento)
                    respuestas_ia.append(respuesta)
                except Exception as e:
                    error_msg = str(e)
                    if "invalid_api_key" in error_msg.lower():
                        logger.error(f"❌ Error de autenticación en fragmento {idx}")
                        # Intentar refrescar la API key
                        try:
                            logger.info("Intentando refrescar la API key...")
                            self.llm_service.refresh_api_key()
                            logger.info("API key refrescada exitosamente")
                            # Reintentar el procesamiento con la nueva key
                            respuesta = await self.llm_service.process_resumen(fragmento)
                            respuestas_ia.append(respuesta)
                        except Exception as refresh_error:
                            logger.error("Error al refrescar credenciales de autenticación")
                            raise ValueError("Error de autenticación persistente")
                    else:
                        logger.error(f"Error procesando fragmento {idx} de licitación {codigo_licitacion}: {error_msg}")
                        continue

            if not respuestas_ia:
                raise ValueError(f"No se pudo procesar ningún fragmento para la licitación {codigo_licitacion}")

            respuesta_completa_ia = " ".join(respuestas_ia)
            try:
                response_chain_1 = await self.llm_service.process_unification(respuesta_completa_ia)
                json_final = self._limpiar_y_convertir_json(response_chain_1)
            except Exception as e:
                logger.error(f"Error en unificación de respuestas para licitación {codigo_licitacion}: {str(e)}")
                raise

            # Guardar resultado usando el repositorio
            guardado_exitoso = await self.repository.guardar_respuesta_ia(codigo_licitacion, json_final)
            if not guardado_exitoso:
                raise ValueError(f"Error al almacenar datos para la licitación {codigo_licitacion}")

            return {
                "codigo_licitacion": codigo_licitacion,
                "resultado_analisis": json_final
            }

        except Exception as e:
            logger.error(f"Error procesando licitación {codigo_licitacion}: {str(e)}", exc_info=True)
            raise

    def _limpiar_y_convertir_json(self, response_chain_1: str) -> str:
        """
        Limpia y convierte la respuesta a formato JSON
        """
        try:
            logger.debug(f"Longitud de entrada: {len(response_chain_1)} caracteres")
            estructura_final = response_chain_1.strip().replace('```json', '').replace('```', '').replace('\n', '')
            
            logger.debug("Intentando parsear JSON...")
            estructura_final = json.loads(estructura_final)
            json_final = json.dumps(estructura_final, ensure_ascii=False)
            
            logger.debug(f"Longitud de salida: {len(json_final)} caracteres")
            return json_final
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error al decodificar JSON: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"❌ Error inesperado: {str(e)}", exc_info=True)
            raise
    
    async def obtener_documentos(self, codigo_licitacion: str, listas_agrupadas: Dict) -> str:
        """
        Obtiene y procesa los documentos de una licitación
        """
        try:
            if codigo_licitacion not in listas_agrupadas:
                raise ValueError(f"No se encontraron documentos para la licitación {codigo_licitacion}")

            rutas = listas_agrupadas[codigo_licitacion]
            logger.info(f"Procesando {len(rutas)} documentos para la licitación {codigo_licitacion}")
            
            documentos_texto = []
            for idx, ruta in enumerate(rutas, 1):
                try:
                    logger.info(f"Obteniendo contenido del documento {idx}/{len(rutas)}: {ruta}")
                    contenido = await self.repository.obtener_contenido_documento(ruta, codigo_licitacion)
                    if contenido and contenido.strip():
                        logger.info(f"✅ Documento {idx} obtenido exitosamente")
                        # Formatear el contenido del documento para mejor contexto
                        documento_formateado = f"""
=== DOCUMENTO {idx}: {ruta} ===
{contenido.strip()}
{"="*50}"""
                        documentos_texto.append(documento_formateado)
                    else:
                        logger.warning(f"⚠️ Documento {idx} está vacío: {ruta}")
                except Exception as doc_error:
                    logger.error(f"❌ Error al obtener documento {idx}: {str(doc_error)}")
                    continue

            if not documentos_texto:
                raise ValueError("No se pudo obtener contenido de ningún documento")

            return "\n\n".join(documentos_texto)
        except Exception as e:
            logger.error(f"Error obteniendo documentos: {str(e)}")
            raise

    async def procesar_consulta_chatbot(self, codigo_licitacion: str, mensaje: str) -> str:
        """
        Procesa una consulta del chatbot para una licitación específica
        """
        logger.info(f"=== Iniciando procesamiento de licitación: {codigo_licitacion} ===")
        start_time = time.time()
        
        try:
            # Obtener listas agrupadas
            listas_agrupadas = await self.repository.obtener_documentos_procesados()
            if not listas_agrupadas:
                logger.warning("No se encontraron documentos procesados")
                return "No se encontraron documentos para la licitación."

            # Obtener y procesar documentos
            try:
                documentos_texto = await self.obtener_documentos(codigo_licitacion, listas_agrupadas)
            except ValueError as ve:
                logger.warning(str(ve))
                return str(ve)
            except Exception as e:
                logger.error(f"Error procesando documentos: {str(e)}")
                return "Error al procesar los documentos de la licitación."

            # Procesar la consulta con el modelo LLM
            logger.info("Enviando consulta al modelo LLM")
            try:
                resultado = await self.llm_service.process_chatbot_query(
                    input_text=mensaje,
                    documentos_texto=documentos_texto
                )
            except Exception as e:
                logger.error(f"Error en el procesamiento LLM: {str(e)}")
                return "Error al procesar la consulta con el modelo de lenguaje."

            if not resultado or not resultado.strip():
                logger.warning("El modelo no generó una respuesta válida")
                return "No se pudo generar una respuesta basada en los documentos disponibles."

            execution_time = time.time() - start_time
            logger.info(f"✅ Respuesta generada exitosamente en {execution_time:.2f} segundos")
            return resultado

        except Exception as e:
            logger.error(f"Error procesando consulta: {str(e)}", exc_info=True)
            raise ValueError(f"Error al procesar la consulta: {str(e)}")

    async def procesar_licitaciones(self, codigos_licitacion: Optional[List[str]] = None) -> Dict:
        """
        Procesa licitaciones y genera resúmenes. Puede procesar todas las licitaciones o un subconjunto específico.
        
        Args:
            codigos_licitacion: Lista opcional de códigos de licitación a procesar. 
                              Si es None, procesa todas las licitaciones disponibles.
        
        Returns:
            Dict con estadísticas y resultados del procesamiento
        """
        logger.info("=== Iniciando procesamiento de licitaciones ===")
        start_time = time.time()
        
        try:
            # Obtener listas agrupadas
            listas_agrupadas = await self.repository.obtener_documentos_procesados()
            if not listas_agrupadas:
                raise ValueError("No se encontraron licitaciones para procesar")
            
            # Filtrar licitaciones si se especificaron códigos
            if codigos_licitacion:
                listas_filtradas = {
                    codigo: rutas for codigo, rutas in listas_agrupadas.items()
                    if codigo in codigos_licitacion
                }
                if not listas_filtradas:
                    raise ValueError("No se encontraron las licitaciones especificadas")
                listas_agrupadas = listas_filtradas

            logger.info(f"Total de licitaciones a procesar: {len(listas_agrupadas)}")
            resultados = []
            
            for codigo_licitacion, rutas in listas_agrupadas.items():
                try:
                    logger.info(f"Procesando licitación: {codigo_licitacion}")
                    
                    # Verificar si ya existe un resumen
                    respuesta_existente = await self.repository.obtener_respuesta_ia(codigo_licitacion)
                    if respuesta_existente:
                        logger.info(f"Resumen existente para licitación: {codigo_licitacion}")
                        resultados.append({
                            "codigo_licitacion": codigo_licitacion,
                            "estado": "existente",
                            "resultado": respuesta_existente
                        })
                        continue

                    # Obtener y procesar documentos
                    documentos_texto = await self.obtener_documentos(codigo_licitacion, {codigo_licitacion: rutas})
                    if not documentos_texto.strip():
                        raise ValueError("No se encontró contenido en los documentos")

                    # Dividir el texto en fragmentos manejables
                    fragmentos = self.dividir_texto(documentos_texto, 100000)
                    
                    # Procesar cada fragmento
                    respuestas_ia = []
                    for idx, fragmento in enumerate(fragmentos, 1):
                        try:
                            logger.info(f"Procesando fragmento {idx}/{len(fragmentos)}")
                            respuesta = await self.llm_service.process_resumen(fragmento)
                            respuestas_ia.append(respuesta)
                        except Exception as e:
                            logger.error(f"Error procesando fragmento {idx}: {str(e)}")
                            continue

                    if not respuestas_ia:
                        raise ValueError("No se pudo procesar ningún fragmento")

                    # Unificar respuestas y convertir a JSON
                    respuesta_completa = " ".join(respuestas_ia)
                    response_unificada = await self.llm_service.process_unification(respuesta_completa)
                    json_final = self._limpiar_y_convertir_json(response_unificada)
                    
                    # Guardar resultado
                    guardado = await self.repository.guardar_respuesta_ia(codigo_licitacion, json_final)
                    if not guardado:
                        raise ValueError("Error al almacenar el resultado")

                    resultados.append({
                        "codigo_licitacion": codigo_licitacion,
                        "estado": "exitoso",
                        "resultado": json_final
                    })
                    logger.info(f"✅ Licitación {codigo_licitacion} procesada exitosamente")

                except Exception as e:
                    logger.error(f"Error procesando licitación {codigo_licitacion}: {str(e)}")
                    resultados.append({
                        "codigo_licitacion": codigo_licitacion,
                        "estado": "error",
                        "error": str(e)
                    })

            # Generar estadísticas
            total_procesadas = len(resultados)
            exitosas = len([r for r in resultados if r["estado"] == "exitoso"])
            existentes = len([r for r in resultados if r["estado"] == "existente"])
            con_error = len([r for r in resultados if r["estado"] == "error"])

            execution_time = time.time() - start_time
            logger.info(f"Tiempo total de procesamiento: {execution_time:.2f} segundos")
            logger.info("=== Fin procesamiento de licitaciones ===")

            return {
                "total_procesadas": total_procesadas,
                "exitosas": exitosas,
                "existentes": existentes,
                "con_error": con_error,
                "tiempo_ejecucion": f"{execution_time:.2f}s",
                "resultados": resultados
            }

        except Exception as e:
            logger.error(f"Error en procesamiento de licitaciones: {str(e)}", exc_info=True)
            raise 