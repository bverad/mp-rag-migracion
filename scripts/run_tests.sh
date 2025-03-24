#!/bin/bash

# Configurar variables de entorno para testing
export TESTING=true
export PYTHONPATH=/app/src
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
omit =
    */tests/*
    */__pycache__/*
    */__init__.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    pass
    raise ImportError" > .coveragerc

# Ejecutar los tests con pytest
python -m pytest tests/ \
    --html=reports/report.html \
    --self-contained-html \
    --cov=src \
    --cov-report=html:reports/coverage \
    --cov-report=xml:reports/coverage/coverage.xml \
    --cov-report=term-missing \
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
echo -e "\n=== Archivos incluidos en el análisis ===" >> /app/reports/coverage/coverage.txt
coverage debug sys >> /app/reports/coverage/coverage.txt

# Ejecutar pylint y guardar reporte
cd /app/src && pylint . --output-format=parseable > /app/reports/pylint.txt || true

# Ajustar las rutas en el reporte XML de cobertura
sed -i 's|/app/src/|src/|g' /app/reports/coverage/coverage.xml

# Salir con el código de estado de los tests
exit $exit_code 