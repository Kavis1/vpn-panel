# Build stage
FROM python:3.10-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.5.1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Set work directory
WORKDIR /app

# Create empty pyproject.toml if it doesn't exist
COPY pyproject.toml* /app/
RUN if [ ! -f /app/pyproject.toml ]; then \
        echo '[tool.poetry]' > /app/pyproject.toml && \
        echo 'name = "vpn-panel"' >> /app/pyproject.toml && \
        echo 'version = "0.1.0"' >> /app/pyproject.toml && \
        echo 'description = "VPN Panel"' >> /app/pyproject.toml && \
        echo 'authors = ["Your Name <your.email@example.com>"]' >> /app/pyproject.toml && \
        echo '' >> /app/pyproject.toml && \
        echo '[tool.poetry.dependencies]' >> /app/pyproject.toml && \
        echo 'python = "^3.10"' >> /app/pyproject.toml && \
        echo 'fastapi = "^0.68.0"' >> /app/pyproject.toml && \
        echo 'uvicorn = {extras = ["standard"], version = "^0.15.0"}' >> /app/pyproject.toml && \
        echo 'sqlalchemy = "^1.4.23"' >> /app/pyproject.toml && \
        echo 'alembic = "^1.7.4"' >> /app/pyproject.toml && \
        echo 'psycopg2-binary = "^2.9.1"' >> /app/pyproject.toml && \
        echo 'python-jose = {extras = ["cryptography"], version = "^3.3.0"}' >> /app/pyproject.toml && \
        echo 'passlib = {extras = ["bcrypt"], version = "^1.7.4"}' >> /app/pyproject.toml && \
        echo 'python-multipart = "^0.0.5"' >> /app/pyproject.toml && \
        echo 'emails = "^0.6"' >> /app/pyproject.toml && \
        echo 'python-dotenv = "^0.19.0"' >> /app/pyproject.toml && \
        echo 'pydantic = "^1.8.2"' >> /app/pyproject.toml && \
        echo 'python-json-logger = "^2.0.2"' >> /app/pyproject.toml && \
        echo 'gunicorn = "^20.1.0"' >> /app/pyproject.toml && \
        echo 'celery = {extras = ["redis"], version = "^5.2.2"}' >> /app/pyproject.toml && \
        echo 'redis = "^4.1.0"' >> /app/pyproject.toml && \
        echo 'httpx = "^0.22.0"' >> /app/pyproject.toml; \
    fi

# Copy only requirements to cache them in docker layer
COPY poetry.lock* /app/

# Install dependencies
RUN if [ -f /app/poetry.lock ]; then \
        poetry config virtualenvs.create false && \
        poetry install --no-interaction --no-ansi --no-root --only main; \
    else \
        poetry add fastapi uvicorn sqlalchemy alembic psycopg2-binary \
            python-jose[cryptography] passlib[bcrypt] python-multipart \
            emails python-dotenv pydantic python-json-logger gunicorn \
            celery[redis] redis httpx --no-interaction; \
    fi

# Copy project
COPY . /app

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
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

# Install Celery and ensure it's in PATH
RUN pip install celery[redis]==5.2.2 && \
    ln -s /usr/local/bin/celery /usr/bin/celery

# Set environment variables
ENV PYTHONPATH=/app/backend:/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:${PATH}" \
    ALEMBIC_CONFIG=/app/alembic.ini

# Create necessary directories and copy scripts
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
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
