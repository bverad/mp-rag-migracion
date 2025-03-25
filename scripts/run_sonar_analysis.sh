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

# Crear archivo de configuración temporal
echo "sonar.projectKey=${PROJECT_NAME}
sonar.projectName=${PROJECT_NAME}
sonar.projectVersion=${PROJECT_VERSION}

# Configuración básica
sonar.sources=src
sonar.tests=tests
sonar.python.version=3
sonar.host.url=${SONAR_HOST_URL}
sonar.token=${SONAR_AUTH_TOKEN}
sonar.scm.provider=git
sonar.qualitygate.wait=true
sonar.ws.timeout=300
sonar.verbose=true
sonar.log.level=DEBUG
sonar.sourceEncoding=UTF-8

# Configuración de fuentes y exclusiones
sonar.sources=src
sonar.inclusions=**/*.py
sonar.exclusions=**/__pycache__/**,**/*.pyc,**/__init__.py,**/tests/**/*,**/*.html,**/*.css,**/*.js,tests/**/*
sonar.coverage.exclusions=tests/**/*,**/__init__.py,**/__pycache__/**,reports/**/*
sonar.cpd.exclusions=tests/**/*

# Configuración de tests
sonar.tests=tests
sonar.test.inclusions=tests/**/*.py
sonar.test.exclusions=src/**/*

# Configuración de cobertura
sonar.python.coverage.reportPaths=reports/coverage/coverage.xml
sonar.python.coverage.forceReportGeneration=true
sonar.python.coverage.itReportPath=reports/coverage/coverage.xml
sonar.python.coverage.overallReportPath=reports/coverage/coverage.xml

# Configuración de reportes de tests
sonar.python.xunit.reportPath=reports/junit.xml
sonar.python.xunit.skipDetails=false
sonar.python.xunit.pythonReportPath=reports/junit.xml
sonar.test.reportPath=reports/junit.xml

# Configuración adicional
sonar.python.pylint.reportPath=reports/pylint.txt" > sonar-project.properties

# Verificar la configuración antes de ejecutar
echo "=== Verificando configuración ==="
echo "Archivos Python en src/:"
find src -type f -name "*.py" -not -path "*/\.*" -not -path "*/__pycache__/*"

echo "=== Contenido del archivo de configuración ==="
cat sonar-project.properties

# Ejecutar SonarQube Scanner con debug
${SONAR_SCANNER_HOME}/bin/sonar-scanner -Dproject.settings=sonar-project.properties -X

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
        
        echo "=== Archivos Python encontrados pero no analizados ==="
        comm -23 <(sort python_files.txt) <(sort .scannerwork/scanner-report/sources.txt)
    fi
else
    echo "⚠ No se encontró la lista de archivos analizados"
fi

echo "=== Análisis de SonarQube completado ===" 