FROM python:3.10-slim

WORKDIR /app

# Install lightweight dependencies
COPY ["GHL RAG/requirements.txt", "/app/requirements.txt"]
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Pre-cache nomic embedding model inside Docker image for instant queries
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='nomic-ai/nomic-embed-text-v1.5')" || true

# Copy all GHL RAG application files
COPY ["GHL RAG/", "/app/"]

# Expose port (Railway default dynamic PORT)
EXPOSE 7860

# Start FastAPI server
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860}"]
