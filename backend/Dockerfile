FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 1. Création de l'utilisateur et dépendances système
RUN useradd -m myuser
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 2. Installation des dépendances Python (en root pour le cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copie du code
COPY . .

# 4. Gestion des permissions : code en lecture seule, dossier logs inscriptible
RUN mkdir -p /app/logs && \
    chown -R myuser:myuser /app && \
    chmod +x start.sh && \
    chmod -R 555 /app && \
    chmod -R 755 /app/logs

# 5. Passage à l'utilisateur non-privilégié
USER myuser

EXPOSE 8000

# 6. Vérification de santé du conteneur (API + base de données)
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health', timeout=4)" || exit 1

# 7. Lancement du script (attente DB, migrations Alembic, Uvicorn)
CMD ["./start.sh"]
