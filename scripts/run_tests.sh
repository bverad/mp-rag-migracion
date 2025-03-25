#!/bin/bash
set -e

echo "=== Iniciando script de tests ==="
echo "=== Verificando entorno ==="
pwd
ls -la
echo "=== Variables de entorno ==="
env | grep -E "PYTHON|TEST|DEBUG" || true

# Configurar variables de entorno para testing
export TESTING=true
export PYTHONPATH=/app
export DEBUG=true

echo "=== Creando directorios necesarios ==="
mkdir -p /app/reports/coverage
mkdir -p /app/logs
mkdir -p /app/static
ls -la /app/reports/ || true

echo "=== Cambiando al directorio de la aplicación ==="
cd /app
pwd
ls -la

echo "=== Configurando coverage ==="
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

echo "=== Configuración de coverage ==="
cat .coveragerc

echo "=== Ejecutando tests con cobertura ==="
PYTHONPATH=/app python -m pytest tests/unit/ tests/integration/ \
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
    --log-cli-level=INFO \
    --import-mode=importlib

# Verificar el resultado
exit_code=$?

echo "=== Generando reporte detallado de cobertura ==="
echo "=== Reporte Detallado de Cobertura ===" > /app/reports/coverage/coverage.txt
coverage report --show-missing >> /app/reports/coverage/coverage.txt

echo "=== Ajustando rutas en el reporte XML ==="
sed -i 's|/app/src/|src/|g' /app/reports/coverage/coverage.xml
sed -i 's|/app/tests/|tests/|g' /app/reports/coverage/coverage.xml

echo "=== Ajustando rutas en el reporte JUnit ==="
sed -i 's|classname="tests\.|classname="tests/|g' /app/reports/junit.xml
sed -i 's|\.|/|g' /app/reports/junit.xml
sed -i 's|/py"|.py"|g' /app/reports/junit.xml

echo "=== Ejecutando pylint ==="
cd /app/src && pylint . --output-format=parseable > /app/reports/pylint.txt || true

echo "=== Verificando archivos generados ==="
ls -la /app/reports/ || true
ls -la /app/reports/coverage/ || true
ls -la /app/reports/coverage/html/ || true

echo "=== Verificando contenido de archivos clave ==="
echo "=== Inicio de coverage.xml ==="
head -n 20 /app/reports/coverage/coverage.xml || true
echo "=== Inicio de coverage.txt ==="
head -n 20 /app/reports/coverage/coverage.txt || true

echo "=== Verificando ajustes en reportes ==="
echo "Coverage XML - primeras líneas:"
head -n 20 /app/reports/coverage/coverage.xml
echo "JUnit XML - primeras líneas:"
head -n 20 /app/reports/junit.xml

echo "=== Ajustando permisos ==="
chmod -R 777 /app/reports/

echo "=== Verificando reportes ajustados ==="
echo "coverage.xml:"
head -n 20 /app/reports/coverage/coverage.xml
echo "junit.xml:"
head -n 20 /app/reports/junit.xml

echo "=== Script de tests completado con código de salida: ${exit_code} ==="
exit $exit_code 