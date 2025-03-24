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

# Listar todos los archivos Python antes de las pruebas
echo "=== Archivos Python en el proyecto ==="
find . -name "*.py" -not -path "*/\.*" -not -path "*/venv/*"
echo "==========================="

# Configurar coverage para usar rutas relativas
echo "[run]
source = src
branch = True
data_file = .coverage

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    pass
    raise ImportError

[xml]
output = reports/coverage/coverage.xml
relative_files = True" > .coveragerc

# Mostrar la configuración actual de coverage
echo "=== Coverage Configuration ==="
cat .coveragerc
echo "==========================="

# Limpiar archivos de cobertura anteriores
rm -f .coverage*
rm -f reports/coverage/*

# Ejecutar pytest con coverage
echo "=== Ejecutando tests y generando reportes ==="
python -m pytest tests/unit/ tests/integration/ \
    --cov=src \
    --cov-config=.coveragerc \
    --cov-branch \
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

# Generar y mostrar reporte detallado
echo "=== Reporte Detallado de Cobertura ==="
coverage report --show-missing | tee /app/reports/coverage/coverage.txt

# Verificar el contenido del reporte XML
echo "=== Verificando reporte XML ==="
if [ -f "reports/coverage/coverage.xml" ]; then
    echo "El archivo XML existe"
    ls -l reports/coverage/coverage.xml
    echo "Contenido del XML:"
    cat reports/coverage/coverage.xml
else
    echo "ERROR: El archivo XML no existe"
fi

# Verificar archivos incluidos en la cobertura
echo "=== Archivos incluidos en la cobertura ==="
coverage debug sys > /app/reports/coverage/debug.txt
coverage debug config >> /app/reports/coverage/debug.txt
echo "Debug info guardada en /app/reports/coverage/debug.txt"

# Verificar estructura de directorios final
echo "=== Estructura de directorios final ==="
ls -R /app/reports/coverage/

# Ajustar las rutas en el reporte XML
echo "=== Ajustando rutas en el reporte XML ==="
sed -i 's|filename="/app/|filename="|g' /app/reports/coverage/coverage.xml
sed -i 's|/app/src/|src/|g' /app/reports/coverage/coverage.xml

# Ejecutar pylint y guardar reporte
cd /app/src && pylint . --output-format=parseable > /app/reports/pylint.txt || true

# Verificar el resultado final
echo "=== Verificación final del archivo XML ==="
head -n 20 /app/reports/coverage/coverage.xml

# Salir con el código de estado de los tests
exit $exit_code 