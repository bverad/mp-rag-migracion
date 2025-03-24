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
include =
    src/main.py
    src/core/*.py
    src/repositories/*.py
    src/services/*.py
    src/models/*.py
    src/api/*.py
omit =
    */tests/*
    */__pycache__/*
    */__init__.py
    */test_*.py
    tests/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    pass
    raise ImportError" > .coveragerc

# Mostrar la configuración actual de coverage
echo "=== Coverage Configuration ==="
cat .coveragerc
echo "==========================="

# Ejecutar tests con cobertura detallada
python -m pytest tests/ \
    --cov=src \
    --cov-report=xml:reports/coverage/coverage.xml \
    --cov-report=html:reports/coverage/html \
    --cov-report=term-missing \
    --cov-fail-under=80 \
    -v

# Verificar que el archivo XML se generó correctamente
echo "=== Verificando archivo XML de cobertura ==="
ls -l reports/coverage/coverage.xml
echo "=== Primeras líneas del archivo XML ==="
head -n 20 reports/coverage/coverage.xml
echo "==========================="

# Generar reporte detallado
echo "=== Reporte Detallado de Cobertura ===" > reports/coverage/coverage.txt
coverage report --show-missing >> reports/coverage/coverage.txt
echo -e "\n=== Debug de Coverage ===" >> reports/coverage/coverage.txt
coverage debug sys >> reports/coverage/coverage.txt
coverage debug data >> reports/coverage/coverage.txt

# Ejecutar pylint y guardar reporte
cd /app/src && pylint . --output-format=parseable > /app/reports/pylint.txt || true

# Ajustar las rutas en el reporte XML
sed -i 's|/app/src/|src/|g' reports/coverage/coverage.xml

# Verificar el resultado final
echo "=== Verificación final del archivo XML ==="
head -n 20 reports/coverage/coverage.xml

# Salir con el código de estado de los tests
exit_code=$?
exit $exit_code 