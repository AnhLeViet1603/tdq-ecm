#!/bin/sh
set -e

# Make migrations in case
# python manage.py migrate --noinput || true

echo "Starting AI server..."
# Using runserver for simplicity, binding to 8010
exec python manage.py runserver 0.0.0.0:8010
