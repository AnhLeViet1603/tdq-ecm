#!/bin/bash
set -e

# ─────────────────────────────────────────────────────────────
# Entrypoint: promotion service (port 8007)
# ─────────────────────────────────────────────────────────────

DB_HOST=${DB_HOST:-postgres}
DB_PORT=${DB_PORT:-5432}

echo "[$(date -u +%H:%M:%S)] Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
until nc -z "${DB_HOST}" "${DB_PORT}"; do
    sleep 0.5
done
echo "[$(date -u +%H:%M:%S)] PostgreSQL is ready."

echo "[$(date -u +%H:%M:%S)] Creating migrations for app 'promotion'..."
python manage.py makemigrations promotion --noinput || true

echo "[$(date -u +%H:%M:%S)] Applying migrations..."
python manage.py migrate --noinput

echo "[$(date -u +%H:%M:%S)] Starting promotion on port ${SERVICE_PORT:-8007}..."
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${SERVICE_PORT:-8007}" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -