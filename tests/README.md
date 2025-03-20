# Documentación de Pruebas MP-RAG

## Descripción General
Este directorio contiene el conjunto completo de pruebas automatizadas para el proyecto MP-RAG API. Las pruebas están diseñadas para garantizar la calidad del código, mantener la integridad de la aplicación y facilitar el desarrollo continuo.

## Estructura de Pruebas
```plaintext
tests/
├── integration/                    # Pruebas de integración
│   ├── test_endpoints.py           # Pruebas de endpoints API
│   └── test_services.py            # Pruebas de integración entre servicios
├── unit/                           # Pruebas unitarias
│   ├── test_main.py                # Pruebas de configuración FastAPI
│   ├── test_licitacion_service.py
│   ├── test_llm_service.py
│   └── test_mercadopublico_repository.py
├── fixtures/                       # Datos de prueba
│   ├── licitaciones.json
│   └── responses.json
├── conftest.py                     # Configuración y fixtures compartidos
└── README.md                       # Esta documentación
```

## Categorías de Pruebas

### Pruebas Unitarias
Ubicación: `tests/unit/`

#### test_main.py
- Pruebas de configuración de FastAPI
- Validación de middleware CORS
- Configuración de rutas
- Manejo de errores global

#### test_licitacion_service.py
- Procesamiento de licitaciones
- Validación de datos
- Manejo de casos borde
- Transformación de datos

#### test_llm_service.py
- Integración con OpenAI
- Procesamiento de prompts
- Manejo de errores de API
- Validación de respuestas

#### test_mercadopublico_repository.py
- Conexión con API externa
- Caché de respuestas
- Manejo de errores de red
- Transformación de datos

### Pruebas de Integración
Ubicación: `tests/integration/`

#### test_endpoints.py
- Flujos completos de API
- Validación de respuestas
- Manejo de errores HTTP
- Autenticación y autorización

#### test_services.py
- Interacción entre servicios
- Flujos de datos end-to-end
- Manejo de estado
- Validación de resultados

## Configuración de Pruebas

### Variables de Entorno
```env
TESTING=true
OPENAI_API_KEY=test-key-123
DEBUG=true
PORT=5000
USERNAME=test_user
PASSWORD=test_password
EMPRESA_ID=1
```

### Fixtures Compartidos
Ubicación: `conftest.py`

```python
@pytest.fixture
def test_app():
    """Proporciona instancia de FastAPI configurada para pruebas"""
    from src.main import app
    return app

@pytest.fixture
def test_client(test_app):
    """Cliente de prueba para la API"""
    return TestClient(test_app)
```

## Ejecución de Pruebas

### Comandos Principales
```bash
# Todas las pruebas
pytest

# Pruebas específicas
pytest tests/unit/
pytest tests/integration/
pytest tests/unit/test_main.py

# Con cobertura
pytest --cov=src --cov-report=html

# Modo verbose
pytest -v

# Con logs
pytest --log-cli-level=DEBUG
```

### Marcadores Disponibles
```python
@pytest.mark.unit          # Pruebas unitarias
@pytest.mark.integration   # Pruebas de integración
@pytest.mark.slow          # Pruebas lentas
@pytest.mark.api           # Pruebas de API
```

## Mejores Prácticas

### Estructura de Pruebas
```python
@pytest.mark.unit
def test_nombre_funcionalidad():
    """
    Descripción clara de la prueba.
    
    Verifica:
    - Condición específica 1
    - Condición específica 2
    
    Args:
        fixture1: Descripción del fixture
        fixture2: Descripción del fixture
    """
    # Arrange
    datos_entrada = {...}
    
    # Act
    resultado = funcion_a_probar(datos_entrada)
    
    # Assert
    assert resultado == valor_esperado
```

### Convenciones de Nombrado
- Archivos: `test_*.py`
- Funciones: `test_<funcionalidad>_<escenario>`
- Fixtures: `<nombre_descriptivo>`

### Mocking y Simulación
```python
@patch('module.Class')
def test_with_mock(mock_class):
    mock_class.return_value.method.return_value = expected_value
    # Test logic
```

## Métricas y Cobertura

### Requisitos de Cobertura
- Mínimo global: 80%
- Mínimo por módulo: 75%
- Exclusiones documentadas

### Estado Actual
- Cobertura global: 84.16%
- Áreas críticas: 90%+
- Áreas de mejora identificadas

### Reporte de Cobertura
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## Solución de Problemas

### Problemas Comunes

#### 1. Fallos en Pruebas Asíncronas
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result
```

#### 2. Errores de Mocking
```python
# Correcto
with patch('module.function') as mock:
    mock.return_value = expected
    
# Incorrecto
mock = patch('module.function')
mock.return_value = expected  # No funcionará
```

#### 3. Problemas de Cobertura
- Verificar exclusiones en `.coveragerc`
- Revisar imports circulares
- Validar paths de módulos

### Tips de Depuración
1. Usar `pytest -vv` para más detalle
2. Activar logs: `--log-cli-level=DEBUG`
3. Usar `breakpoint()` en puntos críticos
4. Revisar fixtures no utilizados

## Mantenimiento

### Actualización de Pruebas
1. Revisar pruebas al modificar código
2. Actualizar fixtures según necesidad
3. Mantener documentación actualizada
4. Verificar cobertura periódicamente

### Limpieza de Código
1. Remover pruebas obsoletas
2. Actualizar mocks y fixtures
3. Refactorizar pruebas duplicadas
4. Mantener organización clara

## Contribución

### Proceso
1. Crear rama para nuevas pruebas
2. Seguir estructura existente
3. Documentar casos de prueba
4. Mantener cobertura mínima
5. Solicitar revisión de código

### Checklist de PR
- [ ] Pruebas pasan localmente
- [ ] Cobertura cumple mínimos
- [ ] Documentación actualizada
- [ ] Código sigue convenciones
- [ ] Revisión de pares completada 