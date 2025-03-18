from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import time
from typing import Dict, Optional, List
from pydantic import BaseModel
from core.logging import get_logger
from models.licitacion import ChatbotRequest
from services.licitacion_service import LicitacionService
from services.llm_service import LLMService

logger = get_logger(__name__)
router = APIRouter()

class ChatbotRequest(BaseModel):
    codigo_licitacion: str
    mensaje: str

class ResumenRequest(BaseModel):
    codigos_licitacion: Optional[List[str]] = None

def get_services():
    """
    Crea y retorna las instancias de los servicios necesarios.
    """
    try:
        llm_service = LLMService()
        licitacion_service = LicitacionService(llm_service)
        return licitacion_service
    except Exception as e:
        logger.error(f"Error al inicializar servicios: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error al inicializar servicios"
        )

@router.post('/chatbotia')
async def chatbotia_endpoint(
    request: ChatbotRequest,
    licitacion_service: LicitacionService = Depends(get_services)
) -> Dict:
    """
    Endpoint para procesar consultas del chatbot sobre licitaciones.
    
    Args:
        request: Objeto ChatbotRequest con código de licitación y mensaje
        licitacion_service: Instancia del servicio de licitaciones (inyectado)
    
    Returns:
        Dict: Respuesta con el resultado del procesamiento
    
    Raises:
        HTTPException: Si ocurre algún error durante el procesamiento
    """
    request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    logger.info(f"=== Iniciando procesamiento ChatbotIA [Request: {request_id}] ===")
    start_time = time.time()

    try:
        # Validar entrada
        if not request.codigo_licitacion or not request.mensaje:
            raise HTTPException(
                status_code=400,
                detail="Código de licitación y mensaje son requeridos"
            )

        logger.info(f"Procesando solicitud para licitación: {request.codigo_licitacion}")
        logger.debug(f"Mensaje del usuario: {request.mensaje[:100]}..." if request.mensaje else "Sin mensaje")

        # Procesar la consulta
        resultado = await licitacion_service.procesar_consulta_chatbot(
            request.codigo_licitacion,
            request.mensaje
        )

        if not resultado:
            return JSONResponse(
                status_code=404,
                content={
                    "message": "No se encontró información para la licitación especificada"
                }
            )

        execution_time = time.time() - start_time
        logger.info(f"✅ Procesamiento completado exitosamente [Request: {request_id}]")
        logger.info(f"Tiempo total de ejecución: {execution_time:.2f} segundos")
        
        return {
            "message": "Procesamiento completado",
            "resultado": resultado
        }
    
    except HTTPException as he:
        logger.error(f"❌ Error de cliente en chatbotia [Request: {request_id}]: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"❌ Error en chatbotia [Request: {request_id}]: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )
    
    finally:
        logger.info(f"=== Fin procesamiento ChatbotIA [Request: {request_id}] ===\n")

@router.post('/resumenes_licitacion')
async def procesar_licitaciones_endpoint(
    request: ResumenRequest = None,
    licitacion_service: LicitacionService = Depends(get_services)
):
    """
    Endpoint unificado para procesar resúmenes de licitaciones.
    Puede procesar una licitación específica, un conjunto de licitaciones o todas las licitaciones disponibles.
    
    Args:
        request: Objeto ResumenRequest opcional con lista de códigos de licitación
        licitacion_service: Instancia del servicio de licitaciones (inyectado)
    
    Returns:
        JSONResponse con el resultado del procesamiento y estadísticas
    """
    request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    logger.info(f"=== Iniciando procesamiento de licitaciones [Request: {request_id}] ===")
    start_time = time.time()

    try:
        # Procesar licitaciones (todas o específicas)
        codigos_licitacion = request.codigos_licitacion if request and request.codigos_licitacion else None
        if codigos_licitacion:
            logger.info(f"Procesando licitaciones específicas: {codigos_licitacion}")
        else:
            logger.info("Procesando todas las licitaciones disponibles")

        resultado = await licitacion_service.procesar_licitaciones(codigos_licitacion)

        execution_time = time.time() - start_time
        logger.info(f"✅ Procesamiento completado exitosamente [Request: {request_id}]")
        logger.info(f"Tiempo total de ejecución: {execution_time:.2f} segundos")
        
        return JSONResponse(content={
            "message": "Procesamiento completado",
            "estadisticas": {
                "total_procesadas": resultado["total_procesadas"],
                "exitosas": resultado["exitosas"],
                "existentes": resultado["existentes"],
                "con_error": resultado["con_error"],
                "tiempo_ejecucion": resultado["tiempo_ejecucion"]
            },
            "resultados": resultado["resultados"]
        }, status_code=200)
    
    except Exception as e:
        logger.error(f"❌ Error en procesar_licitaciones [Request: {request_id}]: {str(e)}", exc_info=True)
        return JSONResponse(content={
            "message": "Error en procesamiento de licitaciones",
            "error": str(e)
        }, status_code=500)
    
    finally:
        logger.info(f"=== Fin procesamiento de licitaciones [Request: {request_id}] ===\n") 