#!/bin/bash
set -ex

# Configurar variables de entorno para testing
export TESTING=true
export PYTHONPATH=/app
export DEBUG=true

# Crear directorios necesarios
mkdir -p /app/reports/coverage
mkdir -p /app/logs
mkdir -p /app/static

# Cambiar al directorio de la aplicación
cd /app

# Configurar coverage para usar rutas relativas
echo "[run]
source = src/
relative_files = True
branch = True
parallel = True
concurrency = multiprocessing

[paths]
source =
    src/
    /app/src/

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    pass
    raise ImportError

[xml]
output = reports/coverage/coverage.xml" > .coveragerc

# Mostrar la configuración actual de coverage
echo "=== Coverage Configuration ==="
cat .coveragerc
echo "==========================="

# Listar archivos Python en src para verificar
echo "=== Python files in src ==="
find src -name "*.py" -not -path "*/\.*"
echo "==========================="

# Ejecutar todos los tests con cobertura
echo "=== Ejecutando tests y generando reportes ==="
python -m pytest tests/unit/ tests/integration/ \
    --cov=src \
    --cov-config=.coveragerc \
    --cov-report=xml:reports/coverage/coverage.xml \
    --cov-report=html:reports/coverage/html \
    --cov-report=term-missing \
    --html=reports/report.html \
    --self-contained-html \
    --junitxml=reports/junit.xml \
    -v \
    --tb=short \
    --capture=no \
    --log-cli-level=INFO

# Verificar el resultado
exit_code=$?

# Generar reporte detallado de cobertura
echo "=== Reporte Detallado de Cobertura ===" > /app/reports/coverage/coverage.txt
coverage report --show-missing >> /app/reports/coverage/coverage.txt

# Mostrar el contenido del reporte para verificación
echo "=== Contenido del reporte de cobertura ==="
cat /app/reports/coverage/coverage.txt
echo "========================================="

# Ajustar las rutas en el reporte XML de cobertura
sed -i 's|/app/src/|src/|g' /app/reports/coverage/coverage.xml

# Verificar el contenido del XML
echo "=== Verificación del archivo XML ==="
echo "Primeras 20 líneas del XML:"
head -n 20 /app/reports/coverage/coverage.xml
echo "========================================="
echo "Buscando entradas de servicios en el XML:"
grep -A 2 "services/" /app/reports/coverage/coverage.xml || true
echo "========================================="

# Ejecutar pylint y guardar reporte
cd /app/src && pylint . --output-format=parseable > /app/reports/pylint.txt || true

# Verificar el resultado final
echo "=== Verificación final del archivo XML ==="
head -n 20 /app/reports/coverage/coverage.xml

# Salir con el código de estado de los tests
exit $exit_code 