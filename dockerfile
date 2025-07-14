# Python 3.11 als Base Image
FROM python:3.11-slim

# Arbeitsverzeichnis erstellen
WORKDIR /app

# System-Dependencies installieren
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Requirements kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bot-Code kopieren
COPY main.py .

# Security: Non-root user erstellen
RUN useradd -m -u 1001 botuser
RUN chown -R botuser:botuser /app
USER botuser

# Port für Health Check
EXPOSE 8080

# Umgebungsvariablen
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Bot starten
CMD ["python", "main.py"]
