# Documentación de Pruebas

## Descripción General

Este directorio contiene el conjunto de pruebas para el proyecto MP-RAG API. Las pruebas están organizadas en diferentes categorías y utilizan pytest como framework de pruebas.

## Estructura de Pruebas

```
tests/
├── integration/           # Pruebas de integración
│   └── test_endpoints.py  # Pruebas de integración de endpoints API
├── unit/                 # Pruebas unitarias
│   ├── test_main.py      # Pruebas para la aplicación principal
│   ├── test_licitacion_service.py
│   ├── test_llm_service.py
│   └── test_mercadopublico_repository.py
├── conftest.py          # Configuración y fixtures compartidos
└── README.md            # Este archivo de documentación
```

## Categorías de Pruebas

### Pruebas Unitarias
- `test_main.py`: Pruebas para la configuración y configuración de la aplicación FastAPI
- `test_licitacion_service.py`: Pruebas para el servicio de procesamiento de licitaciones
- `test_llm_service.py`: Pruebas para el servicio de modelos de lenguaje
- `test_mercadopublico_repository.py`: Pruebas para el repositorio de datos

### Pruebas de Integración
- `test_endpoints.py`: Pruebas de extremo a extremo para endpoints API

## Ejecución de Pruebas

### Ejecutar Todas las Pruebas
```bash
pytest
```

### Ejecutar Categorías Específicas de Pruebas
```bash
# Ejecutar solo pruebas unitarias
pytest tests/unit/

# Ejecutar solo pruebas de integración
pytest tests/integration/

# Ejecutar un archivo específico de pruebas
pytest tests/unit/test_main.py
```

### Ejecutar con Cobertura
```bash
# Ejecutar pruebas con reporte de cobertura
pytest --cov=src --cov-report=html

# Abrir reporte de cobertura
open htmlcov/index.html
```

## Configuración de Pruebas

### Variables de Entorno
Las pruebas utilizan variables de entorno definidas en `conftest.py`. Asegúrese de que estén correctamente configuradas:
- PORT
- DEBUG
- EMPRESA_ID
- OPENAI_API_KEY

### Marcadores
Los siguientes marcadores están disponibles para categorización de pruebas:
- `@pytest.mark.unit`: Pruebas unitarias
- `@pytest.mark.integration`: Pruebas de integración
- `@pytest.mark.slow`: Pruebas lentas
- `@pytest.mark.api`: Pruebas relacionadas con API

## Escribir Nuevas Pruebas

### Directrices
1. Seguir la estructura y convenciones de nombres existentes
2. Incluir docstrings apropiados explicando el propósito y las aserciones
3. Utilizar fixtures apropiados de `conftest.py`
4. Simular dependencias externas
5. Manejar operaciones asíncronas correctamente

### Estructura de Ejemplo de Prueba
```python
@pytest.mark.unit
def test_nombre_funcionalidad():
    """
    Descripción de la prueba.
    
    Verifica que:
    - Se cumple la condición 1
    - Se cumple la condición 2
    """
    # Preparar
    # Actuar
    # Verificar
```

## Requisitos de Cobertura

- Requisito mínimo de cobertura: 80%
- Cobertura actual: 84.16%
- Áreas que necesitan mejora:
  - main.py (0% cobertura)
  - routes.py (85% cobertura)
  - mercadopublico_repository.py (80% cobertura)

## Solución de Problemas

### Problemas Comunes
1. **Fallos en Pruebas Asíncronas**
   - Asegurar uso correcto de `@pytest.mark.asyncio`
   - Verificar configuración del bucle de eventos

2. **Problemas con Mocks**
   - Verificar valores de retorno de mocks
   - Comprobar aserciones de llamadas a mocks

3. **Problemas de Cobertura**
   - Revisar rutas excluidas
   - Verificar rutas de ejecución de pruebas

### Consejos de Depuración
1. Usar `pytest -vv` para salida detallada
2. Habilitar logging con `--log-cli-level=DEBUG`
3. Usar `breakpoint()` para depuración
4. Revisar reportes de cobertura para líneas no cubiertas 