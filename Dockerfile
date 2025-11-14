# Imagen base ligera de Python
FROM python:3.11-slim

# Configurar el entorno de trabajo
WORKDIR /app

# Copiar dependencias primero (para aprovechar caché de Docker)
COPY requirements.txt .

# Restaurar repositorios de Debian e instalar dependencias
RUN echo "deb http://deb.debian.org/debian bookworm main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://deb.debian.org/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://deb.debian.org/debian bookworm-updates main contrib non-free" >> /etc/apt/sources.list && \
    apt-get -o Acquire::ForceIPv4=true update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libssl-dev \
        libffi-dev \
        build-essential \
        default-libmysqlclient-dev \
        pkg-config && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copiar el resto del proyecto
COPY . .

# Variable de entorno para Python
ENV PYTHONUNBUFFERED=1

# Exponer el puerto del backend Flask (Railway lo asignará automáticamente)
EXPOSE 5000

# Comando de ejecución
CMD ["python", "run.py"]