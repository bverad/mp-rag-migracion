from typing import List, Dict, Any, Optional
import requests
from datetime import datetime
import time
from core.config import settings
from core.logging import get_logger
import urllib3
from models.licitacion import Licitacion, Documento
import logging
import aiohttp
import json
import ssl

# Deshabilitar advertencias de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Crear un contexto SSL que no verifique certificados
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

logger = get_logger(__name__)

class MercadoPublicoRepository:
    def __init__(self, testing: bool = False):
        self.testing = testing
        self.session = requests.Session()
        self.session.verify = False  # Deshabilitar verificación SSL
        self.token = None
        self.token_expiry = None
        self.base_url = settings.BASE_URL
        self.endpoints = {
            "documentos_procesados": settings.DOCUMENTOS_PROCESADOS_URL,
            "documento_content": settings.DOCUMENTO_CONTENT_URL,
            "respuesta_ia": settings.OBTENER_RESPUESTA_IA_URL,
            "guardar_respuesta": settings.GUARDAR_RESPUESTA_IA_URL
        }
        
        # Configuración SSL para aiohttp
        self.ssl_context = ssl_context
        
        if not testing:
            self._authenticate()
        else:
            # En modo testing, configurar un token de prueba
            self.token = "test_token"
            self.token_expiry = datetime.now().timestamp() + 3600
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            })

    def _authenticate(self) -> None:
        """Autentica con el servicio de Mercado Público"""
        try:
            auth_data = {
                "username": settings.USERNAME,
                "password": settings.PASSWORD,
                "empresa_id": int(settings.EMPRESA_ID)  # Asegurar que sea entero
            }
            
            logger.info(f"Intentando autenticar con usuario: {settings.USERNAME} y empresa_id: {auth_data['empresa_id']}")
            
            # Agregar headers específicos para la autenticación
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            response = self.session.post(
                settings.AUTH_URL,
                json=auth_data,
                headers=headers,
                verify=False
            )
            
            # Log detallado de la respuesta
            logger.info(f"Respuesta de autenticación: {response.status_code}")
            logger.info(f"Headers de respuesta: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                logger.info(f"Respuesta del servidor: {response_data}")
            except json.JSONDecodeError:
                logger.error(f"Respuesta no JSON: {response.text}")
                raise ValueError("Respuesta del servidor no es JSON válido")
            
            if response.status_code != 200:
                error_msg = response_data.get('msg', 'Error desconocido')
                logger.error(f"Error de autenticación: {error_msg}")
                raise ValueError(f"Error de autenticación: {response.status_code} - {error_msg}")
            
            if not response_data:
                logger.error("Respuesta vacía del servidor")
                raise ValueError("Respuesta vacía del servidor")
                
            # Buscar el token en la respuesta
            token = response_data.get("access_token") or response_data.get("token")
            if not token:
                logger.error(f"Respuesta sin token: {response_data}")
                raise ValueError("No se recibió token de autenticación")
                
            self.token = token
            self.token_expiry = datetime.now().timestamp() + 3600  # 1 hora
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            })
            logger.info("✅ Autenticación exitosa")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error de conexión en autenticación: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ Error en autenticación: {str(e)}")
            raise

    def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Realiza una petición HTTP con manejo de errores"""
        try:
            if not self.testing and (not self.token or datetime.now().timestamp() >= self.token_expiry):
                self._authenticate()
                
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Error en petición HTTP: {str(e)}")
            raise

    async def obtener_documentos_procesados(self) -> Dict[str, List[str]]:
        """
        Obtiene y agrupa los documentos procesados por código de licitación
        """
        try:
            if self.testing:
                return {"test_code": ["test_path"]}

            async with aiohttp.ClientSession(headers=self.session.headers) as session:
                async with session.get(self.endpoints["documentos_procesados"], ssl=self.ssl_context) as response:
                    if response.status == 200:
                        datos = await response.json()
                        
                        # Agrupar por código de licitación
                        listas_agrupadas = {}
                        for dato in datos:
                            codigo = dato.get('codigo_licitacion')
                            ruta = dato.get('ruta_documento')
                            
                            if codigo and ruta:
                                if codigo not in listas_agrupadas:
                                    listas_agrupadas[codigo] = []
                                listas_agrupadas[codigo].append(ruta)
                        
                        logger.info(f"Total de licitaciones agrupadas: {len(listas_agrupadas)}")
                        return listas_agrupadas
                    else:
                        logger.error(f"Error al obtener documentos procesados: {response.status}")
                        return {}

        except Exception as e:
            logger.error(f"Error en obtener_documentos_procesados: {str(e)}", exc_info=True)
            return {}

    async def obtener_contenido_documento(self, ruta: str, codigo_licitacion: str) -> str:
        """
        Obtiene el contenido de un documento específico
        """
        try:
            if self.testing:
                return "Test content"

            params = {
                "ruta_documento": ruta,
                "codigo_licitacion": codigo_licitacion
            }

            async with aiohttp.ClientSession(headers=self.session.headers) as session:
                async with session.get(self.endpoints["documento_content"], params=params, ssl=self.ssl_context) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("contenido", "")
                    else:
                        logger.error(f"Error al obtener contenido del documento: {response.status}")
                        return ""

        except Exception as e:
            logger.error(f"Error en obtener_contenido_documento: {str(e)}", exc_info=True)
            return ""

    async def obtener_respuesta_ia(self, codigo_licitacion: str) -> Optional[Dict]:
        """
        Verifica si existe una respuesta IA para una licitación
        """
        try:
            if self.testing:
                return None

            params = {"codigo_licitacion": codigo_licitacion}
            
            async with aiohttp.ClientSession(headers=self.session.headers) as session:
                async with session.get(self.endpoints["respuesta_ia"], params=params, ssl=self.ssl_context) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        return None
                    else:
                        logger.error(f"Error al verificar respuesta IA: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Error en obtener_respuesta_ia: {str(e)}", exc_info=True)
            return None

    async def guardar_respuesta_ia(self, codigo_licitacion: str, resultado_analisis: str) -> bool:
        """
        Guarda el resultado del análisis de una licitación
        """
        try:
            if self.testing:
                return True

            data = {
                "codigo_licitacion": codigo_licitacion,
                "resultado_analisis": resultado_analisis
            }

            async with aiohttp.ClientSession(headers=self.session.headers) as session:
                async with session.post(self.endpoints["guardar_respuesta"], json=data, ssl=self.ssl_context) as response:
                    if response.status == 200:
                        logger.info(f"Respuesta IA guardada exitosamente para licitación {codigo_licitacion}")
                        return True
                    else:
                        logger.error(f"Error al guardar respuesta IA: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Error en guardar_respuesta_ia: {str(e)}", exc_info=True)
            return False 