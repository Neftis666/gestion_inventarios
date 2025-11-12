# Imagen base ligera de Python
FROM python:3.11-slim

# Configurar el entorno de trabajo
WORKDIR /app

# Copiar dependencias
COPY requirements.txt .

# Restaurar los repositorios de Debian, instalar dependencias y paquetes necesarios
RUN echo "deb http://deb.debian.org/debian bookworm main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://deb.debian.org/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://deb.debian.org/debian bookworm-updates main contrib non-free" >> /etc/apt/sources.list && \
    apt-get -o Acquire::ForceIPv4=true update && \
    apt-get install -y --no-install-recommends gcc libssl-dev libffi-dev build-essential && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copiar el resto del proyecto
COPY . .

# Exponer el puerto del backend Flask
EXPOSE 5000

# Comando de ejecución
CMD ["python", "run.py"]
