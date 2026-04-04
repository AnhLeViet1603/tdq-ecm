#!/bin/bash
set -e

# ─────────────────────────────────────────────────────────────
# Entrypoint: gateway service (port 8000)
# No database — serves frontend + reverse-proxies to microservices
# ─────────────────────────────────────────────────────────────

echo "[$(date -u +%H:%M:%S)] Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "[$(date -u +%H:%M:%S)] Starting gateway on port ${SERVICE_PORT:-8000}..."
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${SERVICE_PORT:-8000}" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --threads 4 \
    --timeout 30 \
    --access-logfile - \
    --error-logfile -