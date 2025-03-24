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

# Configurar coverage para usar rutas relativas y mostrar todos los archivos
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

# Ejecutar todos los tests con cobertura
python -m pytest tests/ \
    --cov=src \
    --cov-report=xml:reports/coverage/coverage.xml \
    --cov-report=html:reports/coverage/html \
    --cov-report=term-missing \
    --cov-fail-under=80 \
    -v

# Verificar el resultado
exit_code=$?

# Generar reporte detallado de cobertura
echo "=== Reporte Detallado de Cobertura ===" > /app/reports/coverage/coverage.txt
coverage report --show-missing >> /app/reports/coverage/coverage.txt
echo -e "\n=== Archivos incluidos en el análisis ===" >> /app/reports/coverage/coverage.txt
coverage debug sys >> /app/reports/coverage/coverage.txt

# Ejecutar pylint y guardar reporte
cd /app/src && pylint . --output-format=parseable > /app/reports/pylint.txt || true

# Ajustar las rutas en el reporte XML de cobertura
sed -i 's|/app/src/|src/|g' /app/reports/coverage/coverage.xml

# Salir con el código de estado de los tests
exit $exit_code 