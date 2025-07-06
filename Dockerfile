# Base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY pyproject.toml .
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install uvicorn gunicorn && \
    if [ -f requirements.txt ]; then pip install -r requirements.txt; fi && \
    pip install -e .

# Copy the rest of the application
COPY . .

# Create non-root user
RUN addgroup --system appuser && adduser --system --no-create-home --group appuser

# Set ownership and permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Command to run the application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--log-level", "info"]
