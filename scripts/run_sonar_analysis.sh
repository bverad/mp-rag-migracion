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

echo "=== Recolectando información diagnóstica ==="
echo "1. Estructura completa del proyecto:"
tree -I '__pycache__|*.pyc|.git|.pytest_cache|.scannerwork|reports'

echo -e "\n2. Archivos Python en el proyecto:"
echo "=== Todos los archivos Python ==="
find . -type f -name "*.py" -not -path "*/\.*" -not -path "*/__pycache__/*" | tee all_python_files.txt
echo "Total archivos Python: $(wc -l < all_python_files.txt)"

echo -e "\n=== Archivos Python en src/ ==="
find src -type f -name "*.py" -not -path "*/\.*" -not -path "*/__pycache__/*" | tee src_python_files.txt
echo "Total archivos Python en src/: $(wc -l < src_python_files.txt)"

echo -e "\n3. Verificando reporte de cobertura:"
if [ -f "reports/coverage/coverage.xml" ]; then
    echo "=== Primeras 50 líneas del reporte de cobertura ==="
    head -n 50 reports/coverage/coverage.xml
    
    echo -e "\n=== Archivos en el reporte de cobertura ==="
    grep -A 1 "<class" reports/coverage/coverage.xml
else
    echo "⚠ No se encontró el reporte de cobertura"
fi

echo -e "\n4. Verificando permisos:"
echo "=== Permisos en src/ ==="
ls -lR src/
echo -e "\n=== Permisos en reports/ ==="
ls -lR reports/

echo "=== Generando lista de archivos Python ==="
# Crear lista de archivos Python en src/
find src -type f -name "*.py" -not -path "*/\.*" -not -path "*/__pycache__/*" > src_files.txt
echo "Archivos Python encontrados en src/:"
cat src_files.txt

# Crear archivo de configuración temporal
echo -e "\n=== Creando configuración de SonarQube ==="
echo "sonar.projectKey=${PROJECT_NAME}
sonar.projectName=${PROJECT_NAME}
sonar.projectVersion=${PROJECT_VERSION}

# Configuración básica
sonar.sourceEncoding=UTF-8
sonar.python.version=3
sonar.host.url=${SONAR_HOST_URL}
sonar.token=${SONAR_AUTH_TOKEN}
sonar.scm.provider=git
sonar.qualitygate.wait=true
sonar.ws.timeout=300
sonar.verbose=true
sonar.log.level=DEBUG

# Configuración de fuentes
sonar.sources=src
sonar.inclusions=src/api/**/*.py,src/core/**/*.py,src/models/**/*.py,src/repositories/**/*.py,src/services/**/*.py,src/main.py
sonar.exclusions=**/__pycache__/**,**/*.pyc,**/__init__.py

# Configuración de tests
sonar.tests=tests
sonar.test.inclusions=tests/**/*.py
sonar.test.exclusions=src/**/*

# Configuración de cobertura
sonar.python.coverage.reportPaths=reports/coverage/coverage.xml
sonar.coverage.exclusions=tests/**/*,**/__init__.py,**/__pycache__/**,reports/**/*

# Configuración de reportes
sonar.python.xunit.reportPath=reports/junit.xml
sonar.python.xunit.skipDetails=false

# Configuración adicional
sonar.sourceEncoding=UTF-8" > sonar-project.properties

echo "=== Contenido de sonar-project.properties ==="
cat sonar-project.properties

echo -e "\n=== Verificando archivos antes del análisis ==="
echo "Contenido de src/:"
ls -R src/

echo -e "\n=== Verificando archivos Python en src/ ==="
find src -type f -name "*.py" -not -path "*/\.*" -not -path "*/__pycache__/*" -not -name "__init__.py"

echo -e "\n=== Ejecutando SonarQube Scanner con debug ==="
${SONAR_SCANNER_HOME}/bin/sonar-scanner -Dproject.settings=sonar-project.properties -X

echo -e "\n=== Verificando resultados ==="
if [ -f ".scannerwork/scanner-report/sources.txt" ]; then
    echo "Archivos analizados por SonarQube:"
    cat .scannerwork/scanner-report/sources.txt
    echo -e "\nComparando con archivos originales:"
    echo "Archivos en src_files.txt:"
    cat src_files.txt
    echo -e "\nArchivos faltantes:"
    comm -23 <(sort src_files.txt) <(sort .scannerwork/scanner-report/sources.txt)
fi

if [ -f ".scannerwork/scanner-report/analysis.log" ]; then
    echo -e "\n=== Log de análisis ==="
    echo "Buscando mensajes relevantes:"
    grep -i "exclu\|inclu\|error\|warn\|debug" .scannerwork/scanner-report/analysis.log
fi

echo "=== Análisis completado ===" 