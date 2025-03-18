from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Documento(BaseModel):
    nombre: str
    ruta: str
    contenido: Optional[str] = None

class Licitacion(BaseModel):
    codigo_licitacion: str
    documentos: List[Documento] = []
    fecha_procesamiento: Optional[datetime] = None

class ResumenIA(BaseModel):
    resumen: str
    personal_requerido: List[dict]
    habilidades: List[dict]
    certificaciones: List[dict]
    horas_requeridas: str
    tecnologias: List[dict]
    requisitos_comerciales: List[dict]

class ChatbotRequest(BaseModel):
    codigo_licitacion: str
    mensaje: str

class ResumenLicitacion(BaseModel):
    codigo_licitacion: str = Field(..., description="Código de la licitación")
    resumen_general: str = Field(..., description="Resumen general de la licitación")
    resumen_tecnico: str = Field(..., description="Resumen técnico detallado")
    fecha_generacion: datetime = Field(default_factory=datetime.now, description="Fecha de generación del resumen") 