FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860

WORKDIR /app

# Install system build dependencies and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY ["requirements.txt", "/app/requirements.txt"]
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Pre-cache FastEmbed nomic embedding model inside Docker image (optional cache)
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='nomic-ai/nomic-embed-text-v1.5')" || true

# Copy all GHL RAG application files into /app
COPY ["XortLogix High Level/", "/app/"]
COPY ["start.py", "/app/start.py"]

EXPOSE 7860

CMD ["python", "start.py"]
