# MP-RAG API

## Descripción
MP-RAG API es una aplicación backend desarrollada en Python que proporciona una interfaz REST para procesar y analizar licitaciones del Mercado Público utilizando técnicas de RAG (Retrieval Augmented Generation) y LLMs. La aplicación está diseñada para escalar horizontalmente y proporcionar análisis detallado de licitaciones usando tecnologías de IA avanzadas.

## Tabla de Contenidos
- [Características](#características)
- [Arquitectura](#arquitectura)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [API](#api)
- [Pruebas](#pruebas)
- [Monitoreo y Logging](#monitoreo-y-logging)
- [Seguridad](#seguridad)
- [Despliegue](#despliegue)
- [Contribución](#contribución)
- [Licencia](#licencia)
- [Contacto](#contacto)

## Características
- Procesamiento de licitaciones del Mercado Público
- Generación de resúmenes utilizando LLMs
- Autenticación JWT y manejo seguro de sesiones
- Rate limiting y protección contra ataques comunes
- Sistema de caché distribuido para optimizar rendimiento
- Documentación automática con OpenAPI/Swagger
- Pruebas unitarias y de integración con cobertura mínima del 80%
- Monitoreo y logging detallado con rotación de logs
- Soporte para operaciones asíncronas
- Configuración CORS para seguridad
- Despliegue automatizado en Kubernetes
- Pipeline CI/CD completo

## Arquitectura
### Componentes Principales
- **API Layer**: FastAPI para manejo de endpoints
- **Service Layer**: Lógica de negocio y procesamiento
- **Repository Layer**: Acceso a datos y APIs externas
- **LLM Integration**: Integración con modelos de lenguaje
- **Caching Layer**: Sistema de caché distribuido

### Tecnologías Utilizadas
- **Framework**: FastAPI 0.100+
- **LLM**: LangChain 0.3.19
- **Base de Datos**: PostgreSQL (opcional)
- **Cache**: Redis/Memcached
- **Contenedorización**: Docker
- **Orquestación**: Kubernetes

## Requisitos
### Software
- Python 3.11+
- Docker y Docker Compose
- Kubernetes (para despliegue)
- Git

### Dependencias Principales
```plaintext
Flask==2.1.2
langchain==0.3.19
requests==2.32.3
urllib3==2.2.3
tiktoken==0.8.0
langchain_openai==0.3.7
python-dotenv==1.0.1
langchain-community==0.3.18
werkzeug==2.0.3
scikit-learn>=1.0.2
numpy>=1.21.0
cachetools==5.3.2
```

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/bverad/mp-rag-migracion.git
cd mp-rag-migracion
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

### Variables de Entorno
Crear archivo `.env` en la raíz del proyecto:

```env
# API Configuration
PORT=5000
DEBUG=False
APP_ENV=production

# OpenAI Configuration
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0

# Authentication
USERNAME=your-username
PASSWORD=your-password
EMPRESA_ID=1

# API URLs
API_BASE_URL=https://backendlicitaciones.activeit.com
```

### Configuración del Entorno
```bash
python scripts/setup_env.py
```

## API

### Endpoints Principales

#### Chatbot IA
- **POST** `/chatbotia`
  - Procesa consultas sobre licitaciones usando IA
  - Payload:
    ```json
    {
        "codigo_licitacion": "string",
        "mensaje": "string"
    }
    ```
  - Respuesta:
    ```json
    {
        "message": "Procesamiento completado",
        "resultado": "string"
    }
    ```

#### Resúmenes de Licitaciones
- **POST** `/resumenes_licitacion`
  - Genera resúmenes de licitaciones
  - Payload opcional:
    ```json
    {
        "codigos_licitacion": ["string"]
    }
    ```
  - Respuesta:
    ```json
    {
        "message": "Procesamiento completado",
        "estadisticas": {
            "total_procesadas": "int",
            "exitosas": "int",
            "existentes": "int",
            "con_error": "int",
            "tiempo_ejecucion": "float"
        },
        "resultados": []
    }
    ```

### Documentación API
- Swagger UI: `http://localhost:5000/docs`
- OpenAPI JSON: `http://localhost:5000/openapi.json`

## Monitoreo y Logging

### Sistema de Logging
- Rotación automática de logs (10MB por archivo)
- Retención de 5 archivos de backup
- Niveles configurables de logging
- Formato estructurado de logs
- Ubicación: `/logs/mp_rag.log`

### Formato de Logs
```plaintext
YYYY-MM-DD HH:MM:SS [LEVEL] [module:function:line] Message
```

### Monitoreo
- Health checks en endpoint raíz
- Métricas de rendimiento
- Probes de Kubernetes configurados

## Seguridad

### CORS
- Orígenes permitidos configurados
- Métodos HTTP permitidos
- Credenciales permitidas
- Tiempo de caché preflight: 600s

### Autenticación
- JWT para autenticación de endpoints
- Validación de API keys
- Rate limiting implementado

### Kubernetes
- Límites de recursos configurados
- Probes de salud
- Secrets gestionados de forma segura

## Despliegue

### Docker
```bash
# Construir imagen
docker build -t mp-rag .

# Ejecutar contenedor
docker run -p 5000:5000 mp-rag
```

### Kubernetes
```bash
# Aplicar configuración
kubectl apply -f k8s/deployment.yaml
```

## Contribución

### Flujo de Trabajo
1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/NuevaFuncionalidad`)
3. Desarrollar cambios
4. Ejecutar pruebas (`pytest`)
5. Commit cambios (`git commit -m 'feat: nueva funcionalidad'`)
6. Push a la rama (`git push origin feature/NuevaFuncionalidad`)
7. Crear Pull Request

### Convenciones de Código
- Seguir PEP 8
- Documentar en español
- Mantener cobertura > 80%
- Usar tipos estáticos

### Estructura de Commits
```
<tipo>(<alcance>): <descripción>

<cuerpo>

<pie>
```

Tipos de commit:
- feat: Nueva característica
- fix: Corrección de bug
- docs: Cambios en documentación
- style: Cambios de formato
- refactor: Refactorización
- test: Cambios en pruebas
- chore: Cambios en build

## Licencia
Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## Contacto
Equipo de Desarrollo - desarrollo@activeit.com

Repositorio: [https://github.com/bverad/mp-rag-migracion](https://github.com/bverad/mp-rag-migracion)
