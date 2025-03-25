#!/bin/bash
set -e

echo "=== Iniciando análisis de SonarQube ==="

# Verificar variables de entorno requeridas
if [ -z "$SONAR_HOST_URL" ]; then
    echo "Error: SONAR_HOST_URL no está definida"
    exit 1
fi

if [ -z "$SONAR_AUTH_TOKEN" ]; then
    echo "Error: SONAR_AUTH_TOKEN no está definida"
    exit 1
fi

if [ -z "$SONAR_SCANNER_HOME" ]; then
    echo "Error: SONAR_SCANNER_HOME no está definida"
    exit 1
fi

# Verificar estructura del proyecto
echo "=== Verificando estructura del proyecto ==="
find . -type f -name "*.py" -not -path "*/\.*" -not -path "*/__pycache__/*" > python_files.txt
echo "Archivos Python encontrados:"
cat python_files.txt

echo "=== Verificando reportes de cobertura ==="
if [ -f "reports/coverage/coverage.xml" ]; then
    echo "Reporte de cobertura encontrado"
else
    echo "ADVERTENCIA: No se encontró el reporte de cobertura en reports/coverage/coverage.xml"
fi

# Ejecutar SonarQube Scanner
echo "=== Ejecutando SonarQube Scanner ==="
${SONAR_SCANNER_HOME}/bin/sonar-scanner \
    -Dsonar.projectKey="${PROJECT_NAME}" \
    -Dsonar.projectName="${PROJECT_NAME}" \
    -Dsonar.projectVersion="${PROJECT_VERSION}" \
    -Dsonar.sources=src \
    -Dsonar.python.version=3 \
    -Dsonar.host.url="${SONAR_HOST_URL}" \
    -Dsonar.token="${SONAR_AUTH_TOKEN}" \
    -Dsonar.scm.provider=git \
    -Dsonar.qualitygate.wait=true \
    -Dsonar.ws.timeout=300 \
    -Dsonar.verbose=true \
    -Dsonar.log.level=DEBUG \
    -Dsonar.sourceEncoding=UTF-8 \
    -Dsonar.python.coverage.reportPaths=reports/coverage/coverage.xml \
    -Dsonar.coverage.exclusions=tests/**/*,**/__init__.py,**/__pycache__/**,reports/**/* \
    -Dsonar.test.inclusions=tests/**/*.py \
    -Dsonar.test.exclusions=src/**/* \
    -Dsonar.python.xunit.reportPath=reports/junit.xml \
    -Dsonar.python.xunit.skipDetails=false \
    -Dsonar.inclusions=src/**/*.py \
    -Dsonar.exclusions=**/__pycache__/**,**/*.pyc,**/__init__.py,**/tests/**,**/*.html,**/*.css,**/*.js \
    -Dsonar.python.coverage.forceReportGeneration=true

# Verificar resultados
echo "=== Verificando resultados ==="
if [ -f ".scannerwork/scanner-report/analysis.log" ]; then
    echo "Log de análisis:"
    cat .scannerwork/scanner-report/analysis.log
fi

if [ -f ".scannerwork/scanner-report/sources.txt" ]; then
    echo "Archivos analizados:"
    cat .scannerwork/scanner-report/sources.txt
fi

echo "=== Análisis de SonarQube completado ===" 