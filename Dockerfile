# Imagen base - Actualizada a Python 3.11 para compatibilidad
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY requirements.txt requirements-dev.txt ./

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt

# Verificar la instalación de paquetes críticos
RUN pip list | grep -E "langchain|openai|tiktoken|fastapi|uvicorn"

# Copiar el código fuente
COPY . .

# Crear directorios necesarios
RUN mkdir -p /app/logs && \
    mkdir -p /app/reports && \
    mkdir -p /app/static && \
    chmod -R 777 /app/logs /app/reports /app/static

# Variables de entorno
ENV APP_ENV=production
ENV PYTHONPATH=/app/src
ENV PORT=5000
ENV TESTING=false
ENV DEBUG=false

# Puerto
EXPOSE 5000

# Script para ejecutar tests
COPY scripts/run_tests.sh /app/scripts/run_tests.sh
RUN chmod +x /app/scripts/run_tests.sh

# Comando por defecto para ejecutar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]

# Para ejecutar tests usar:
# docker run --rm -v ${PWD}:/app imagen:tag ./scripts/run_tests.sh