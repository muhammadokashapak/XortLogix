FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY ["GHL RAG/requirements.txt", "/app/requirements.txt"]
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Pre-cache nomic embedding model inside Docker image for fast query initialization
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='nomic-ai/nomic-embed-text-v1.5')" || true

# Copy application files
COPY "GHL RAG" /app/
COPY start_root.py /app/start.py

EXPOSE 7860

CMD ["python", "start.py"]
