#!/bin/sh
set -e

echo "Running Alembic migrations..."
flask db upgrade

echo "Starting Gunicorn..."
exec gunicorn server:app --worker-class gevent --worker-connections 10 --timeout 30 -b 0.0.0.0:8000 --reload --log-syslog