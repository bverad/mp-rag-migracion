#!/bin/bash
set -e

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

# Ejecutar todos los tests con cobertura
echo "=== Ejecutando tests y generando reportes ==="
python -m pytest tests/unit/ tests/integration/ \
    --cov=src \
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

# Ajustar las rutas en el reporte XML de cobertura
sed -i 's|/app/src/|src/|g' /app/reports/coverage/coverage.xml

# Ejecutar pylint y guardar reporte
cd /app/src && pylint . --output-format=parseable > /app/reports/pylint.txt || true

# Verificar el resultado final
echo "=== Verificación final del archivo XML ==="
head -n 20 /app/reports/coverage/coverage.xml

# Salir con el código de estado de los tests
exit $exit_code 