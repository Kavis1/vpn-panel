# Build stage
FROM python:3.10-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -e . && \
    pip install --no-cache-dir uvicorn[standard] gunicorn && \
    # Verify installations
    echo "===== Verifying installations =====" && \
    echo "Python version: $(python --version)" && \
    echo "Pip version: $(pip --version)" && \
    echo "Uvicorn path: $(which uvicorn)" && \
    echo "Uvicorn version: $(python -c \"import uvicorn; print(uvicorn.__version__)\")"

# Runtime stage
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN addgroup --system appuser && adduser --system --no-create-home --group appuser

# Set work directory
WORKDIR /app

# Copy from builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

# Create necessary directories and set permissions
RUN mkdir -p /app/static /app/media /app/logs /app/scripts \
    && chown -R appuser:appuser /app \
    && chmod -R 755 /app/static /app/media /app/logs

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:${PATH}" \
    # Uvicorn settings
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000 \
    UVICORN_WORKERS=2 \
    # Application settings
    ALEMBIC_CONFIG=/app/alembic.ini

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Set environment variables
ENV PYTHONPATH=/app/backend:/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:/usr/bin:${PATH}" \
    # Celery settings
    CELERY_BIN="/usr/local/bin/celery" \
    CELERY_APP="app.worker" \
    CELERY_WORKER_CONCURRENCY=4 \
    CELERY_BEAT_SCHEDULE_FILE="/app/celerybeat-schedule" \
    # Uvicorn settings
    UVICORN_BIN="/usr/local/bin/uvicorn" \
    # Application settings
    ALEMBIC_CONFIG=/app/backend/alembic.ini

# Create necessary directories and set permissions
RUN mkdir -p /app/static /app/media /app/logs /app/scripts \
    && chown -R appuser:appuser /app \
    && chmod -R 755 /app/static /app/media /app/logs

# Copy scripts and make them executable
COPY scripts/* /app/scripts/
RUN chmod +x /app/scripts/*.sh

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
