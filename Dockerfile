FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for psycopg2-binary and general build)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# [OPTIMIZATION] Pre-download FastEmbed model to avoid latency on cold starts
# This adds ~300MB to the image but saves 30-60s on first execution
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='BAAI/bge-small-en-v1.5')"

# Copy the entire project
COPY . .

# Ensure PYTHONPATH includes the current directory for absolute imports
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Cloud Run defaults to port 8080, but we'll use the $PORT env var
EXPOSE 8080

# Run the FastAPI app using uvicorn
# We use uvicorn --port $PORT to allow Cloud Run to override it
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
