#!/bin/bash
set -e

echo "=== Iniciando análisis de SonarQube ==="

# Verificar variables de entorno requeridas
required_vars=(
    "SONAR_HOST_URL"
    "SONAR_AUTH_TOKEN"
    "SONAR_SCANNER_HOME"
    "PROJECT_NAME"
    "PROJECT_VERSION"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: La variable $var no está definida"
        exit 1
    else
        echo "✓ $var está configurada: ${!var}"
    fi
done

# Verificar que el directorio src existe
if [ ! -d "src" ]; then
    echo "Error: No se encuentra el directorio src/"
    pwd
    ls -la
    exit 1
fi

# Verificar estructura del proyecto
echo "=== Verificando estructura del proyecto ==="
echo "Directorio actual: $(pwd)"
echo "Contenido del directorio:"
ls -la

echo "=== Buscando archivos Python ==="
find . -type f -name "*.py" -not -path "*/\.*" -not -path "*/__pycache__/*" > python_files.txt
echo "Archivos Python encontrados:"
cat python_files.txt
total_files=$(wc -l < python_files.txt)
echo "Total de archivos Python encontrados: $total_files"

echo "=== Verificando reportes de cobertura ==="
if [ -f "reports/coverage/coverage.xml" ]; then
    echo "✓ Reporte de cobertura encontrado"
    echo "Contenido del reporte:"
    head -n 10 reports/coverage/coverage.xml
    echo "Verificando rutas en el reporte:"
    grep "filename=" reports/coverage/coverage.xml | head -n 5
else
    echo "⚠ ADVERTENCIA: No se encontró el reporte de cobertura en reports/coverage/coverage.xml"
    echo "Contenido del directorio reports/:"
    ls -la reports/ || true
    echo "Contenido del directorio reports/coverage/:"
    ls -la reports/coverage/ || true
fi

# Ejecutar SonarQube Scanner
echo "=== Ejecutando SonarQube Scanner ==="
echo "Usando scanner en: ${SONAR_SCANNER_HOME}/bin/sonar-scanner"

${SONAR_SCANNER_HOME}/bin/sonar-scanner \
    -Dsonar.projectKey="${PROJECT_NAME}" \
    -Dsonar.projectName="${PROJECT_NAME}" \
    -Dsonar.projectVersion="${PROJECT_VERSION}" \
    -Dsonar.sources=src \
    -Dsonar.tests=tests \
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
    -Dsonar.python.xunit.pythonReportPath=reports/junit.xml \
    -Dsonar.inclusions=src/**/*.py \
    -Dsonar.exclusions=**/__pycache__/**,**/*.pyc,**/__init__.py,**/tests/**,**/*.html,**/*.css,**/*.js \
    -Dsonar.python.coverage.forceReportGeneration=true \
    -Dsonar.python.coverage.itReportPath=reports/coverage/coverage.xml \
    -Dsonar.python.coverage.overallReportPath=reports/coverage/coverage.xml \
    -Dsonar.python.coverage.reportPath=reports/coverage/coverage.xml \
    -Dsonar.test.reportPath=reports/junit.xml \
    -Dsonar.python.xunit.provideDetails=true

# Verificar resultados
echo "=== Verificando resultados ==="
if [ -f ".scannerwork/scanner-report/analysis.log" ]; then
    echo "✓ Log de análisis encontrado"
    echo "Últimas 20 líneas del log:"
    tail -n 20 .scannerwork/scanner-report/analysis.log
else
    echo "⚠ No se encontró el log de análisis"
fi

if [ -f ".scannerwork/scanner-report/sources.txt" ]; then
    echo "✓ Lista de archivos analizados encontrada"
    echo "Archivos analizados:"
    cat .scannerwork/scanner-report/sources.txt
    total_analyzed=$(wc -l < .scannerwork/scanner-report/sources.txt)
    echo "Total de archivos analizados: $total_analyzed"
    
    if [ "$total_analyzed" -lt "$total_files" ]; then
        echo "⚠ ADVERTENCIA: No todos los archivos Python fueron analizados"
        echo "Archivos encontrados: $total_files"
        echo "Archivos analizados: $total_analyzed"
    fi
else
    echo "⚠ No se encontró la lista de archivos analizados"
fi

echo "=== Análisis de SonarQube completado ===" 