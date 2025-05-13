#!/bin/sh
set -e

echo "Running Alembic migrations..."

echo "FLASK ENV"
echo $FLASK_ENV


# flask db upgrade



if [ "$FLASK_ENV" = "testing" ]; then
#   echo "Running tests..."
  exec pytest
else
  pip install gunicorn && pip install gevent
  echo "Starting Gunicorn..."
  exec gunicorn server:app \
    --worker-class gevent \
    --worker-connections 10 \
    --timeout 30 \
    -b 0.0.0.0:8000 \
    --reload \
    --log-syslog
fi
