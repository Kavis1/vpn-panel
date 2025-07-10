#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL is up - continuing"

# Initialize alembic if not already done
if [ ! -d "/app/alembic/versions" ]; then
    echo "Initializing alembic..."
    cd /app
    alembic init -t async alembic
    
    # Copy custom env.py
    if [ -f "/app/backend/alembic/env.py" ]; then
        cp /app/backend/alembic/env.py /app/alembic/
    fi
    
    # Update alembic.ini with database URL
    sed -i "s|sqlalchemy.url =.*|sqlalchemy.url = postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}|" /app/alembic.ini
    
    # Set script location
    sed -i "s|# script_location =.*|script_location = /app/alembic|" /app/alembic.ini
    
    # Set file template
    sed -i "s|# file_template =.*|file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s|" /app/alembic.ini
    
    # Set version location
    sed -i "s|# version_locations =.*|version_locations = /app/backend/alembic/versions|" /app/alembic.ini
fi

# Run migrations
echo "Running database migrations..."
alembic upgrade head

echo "Migrations completed successfully!"
