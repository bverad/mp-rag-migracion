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
find src -name "*.py" -not -path "*/\.*" -not -path "*/venv/*" -not -path "*/__pycache__/*"
echo "==========================="

# Limpiar archivos de cobertura anteriores
rm -f .coverage*
rm -f reports/coverage/*

# Configurar coverage
cat > .coveragerc << EOL
[run]
source = src
branch = True
data_file = .coverage
relative_files = True
omit =
    */venv/*
    */__pycache__/*
    */tests/*
    setup.py

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
    def main()
    if TYPE_CHECKING:

[xml]
output = reports/coverage/coverage.xml
EOL

# Mostrar la configuración actual de coverage
echo "=== Coverage Configuration ==="
cat .coveragerc
echo "==========================="

# Ejecutar pytest con coverage y generar reportes
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
    -v

# Verificar el resultado
exit_code=$?

# Asegurarse que estamos en el directorio correcto
cd /app

# Generar y mostrar reporte detallado
echo "=== Reporte Detallado de Cobertura ==="
coverage combine || true
coverage report --show-missing | tee /app/reports/coverage/coverage.txt

# Regenerar el reporte XML después de combinar
coverage xml -o reports/coverage/coverage.xml

# Verificar el contenido del reporte XML
echo "=== Verificando reporte XML ==="
if [ -f "reports/coverage/coverage.xml" ]; then
    echo "El archivo XML existe"
    ls -l reports/coverage/coverage.xml
    echo "=== Primeras líneas del archivo XML ==="
    head -n 20 reports/coverage/coverage.xml
else
    echo "ERROR: El archivo XML no existe"
    echo "=== Contenido del directorio reports/coverage ==="
    ls -la reports/coverage/
    echo "=== Debug de coverage ==="
    coverage debug sys
    coverage debug data
fi

# Ejecutar pylint
cd /app/src && pylint . --output-format=parseable > /app/reports/pylint.txt || true

# Si el archivo XML existe, ajustar las rutas
if [ -f "/app/reports/coverage/coverage.xml" ]; then
    echo "=== Ajustando rutas en el reporte XML ==="
    cd /app
    # Primero hacemos backup del archivo
    cp reports/coverage/coverage.xml reports/coverage/coverage.xml.bak
    # Ajustamos las rutas
    sed -i 's|filename="/app/src/|filename="src/|g' reports/coverage/coverage.xml
    sed -i 's|filename="/app/|filename="|g' reports/coverage/coverage.xml
    echo "=== Verificando rutas ajustadas ==="
    echo "Primeras 5 líneas con 'filename':"
    grep "filename=" reports/coverage/coverage.xml | head -n 5
    
    # Verificar que el archivo sigue siendo válido XML
    if ! python -c "import xml.etree.ElementTree as ET; ET.parse('reports/coverage/coverage.xml')"; then
        echo "ERROR: El archivo XML quedó inválido después de ajustar las rutas, restaurando backup"
        cp reports/coverage/coverage.xml.bak reports/coverage/coverage.xml
    fi
fi

# Mostrar resumen final
echo "=== Resumen Final ==="
echo "Archivos Python encontrados:"
find src -name "*.py" -not -path "*/\.*" -not -path "*/venv/*" -not -path "*/__pycache__/*" | wc -l
echo "Contenido del reporte de cobertura:"
cat /app/reports/coverage/coverage.txt

exit $exit_code 