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

# Crear directorio para logs
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Variables de entorno
ENV APP_ENV=production
ENV PYTHONPATH=/app
ENV PORT=5000

# Puerto
EXPOSE 5000

# Comando para ejecutar la aplicación con uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "5000"] 