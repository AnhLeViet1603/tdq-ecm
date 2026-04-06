#!/bin/bash

set -e

echo "Starting AI Service..."

# Wait for PostgreSQL using python
echo "Waiting for PostgreSQL..."
until python -c "import psycopg2; psycopg2.connect(host='$DB_HOST', port='$DB_PORT', user='$DB_USER', password='$DB_PASSWORD')" 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is up - executing command"

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Auto-initialize sample data (DISABLED - needs model fixes)
echo "Auto-initializing AI knowledge base... (skipped - model migrations need fixing)"
# if [ -f "/app/auto_init.sh" ]; then
#     chmod +x /app/auto_init.sh
#     /app/auto_init.sh
# fi

# Create vector database directory
echo "Setting up vector database..."
mkdir -p /app/vector_db

# Create ML models directory
echo "Setting up ML models directory..."
mkdir -p /app/ml_models

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:$SERVICE_PORT \
    --workers 3 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
