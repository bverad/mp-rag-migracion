# MP-RAG API

## Descripción
MP-RAG API es una aplicación backend desarrollada en Python que proporciona una interfaz REST para procesar y analizar licitaciones del Mercado Público utilizando técnicas de RAG (Retrieval Augmented Generation) y LLMs.

## Tabla de Contenidos
- [Características](#características)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Pruebas](#pruebas)
- [Documentación API](#documentación-api)
- [Contribución](#contribución)
- [Licencia](#licencia)
- [Contacto](#contacto)

## Características
- Procesamiento de licitaciones del Mercado Público
- Generación de resúmenes utilizando LLMs
- Autenticación JWT
- Rate limiting y protección contra ataques comunes
- Caché para optimizar rendimiento
- Documentación automática con OpenAPI/Swagger
- Pruebas unitarias y de integración con cobertura mínima del 80%
- Monitoreo y logging detallado
- Soporte para operaciones asíncronas
- Configuración CORS para seguridad

## Requisitos
- Python 3.11+
- FastAPI 0.100+
- LangChain 0.3.19+
- OpenAI API Key

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/mp-rag.git
cd mp-rag
```

2. Crear y activar entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Configuración

1. Crear archivo `.env` en la raíz del proyecto:
```env
OPENAI_API_KEY=tu-api-key
PORT=5000
DEBUG=True
USERNAME=tu-usuario
PASSWORD=tu-contraseña
EMPRESA_ID=1
```

2. Configurar el entorno:
```bash
python scripts/setup_env.py
```

## Uso

1. Iniciar el servidor:
```bash
python run.py
```

2. Acceder a la documentación API:
```
http://localhost:5000/docs
```

## Pruebas

### Ejecutar todas las pruebas:
```bash
pytest
```

### Ejecutar pruebas específicas:
```bash
# Pruebas unitarias
pytest tests/unit/

# Pruebas de integración
pytest tests/integration/

# Pruebas de un archivo específico
pytest tests/unit/test_main.py
```

### Generar reporte de cobertura:
```bash
pytest --cov=src --cov-report=html
```

Para más detalles sobre las pruebas, consultar [tests/README.md](tests/README.md).

## Documentación API

La documentación completa de la API está disponible en:
- Swagger UI: `http://localhost:5000/docs`
- OpenAPI JSON: `http://localhost:5000/openapi.json`

### Endpoints Principales

#### Chatbot IA
- `POST /chatbotia`: Procesar consultas del chatbot sobre licitaciones
  - Requiere: código de licitación y mensaje
  - Retorna: Respuesta procesada por IA

#### Resúmenes de Licitaciones
- `POST /resumenes_licitacion`: Procesar resúmenes de licitaciones
  - Opcional: lista de códigos de licitación
  - Retorna: Resúmenes procesados y estadísticas

#### Raíz
- `GET /`: Endpoint de bienvenida y estado del servicio

## Contribución

1. Fork el repositorio
2. Crear una rama para tu feature (`git checkout -b feature/NuevaFuncionalidad`)
3. Asegurar que las pruebas pasan y mantener la cobertura mínima del 80%
4. Commit tus cambios (`git commit -m 'Agregar nueva funcionalidad'`)
5. Push a la rama (`git push origin feature/NuevaFuncionalidad`)
6. Abrir un Pull Request

### Guías de Contribución
- Seguir las convenciones de código existentes
- Documentar todo el código nuevo en español
- Agregar pruebas para toda nueva funcionalidad
- Mantener la cobertura de pruebas por encima del 80%
- Actualizar la documentación según sea necesario

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Nombre del Desarrollador - [@twitter](https://twitter.com/usuario) - email@example.com

Link del Proyecto: [https://github.com/usuario/mp-rag](https://github.com/usuario/mp-rag)
