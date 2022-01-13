#!/bin/bash
set -e

python manage.py migrate
gunicorn --bind 0.0.0.0:8000 \
         --worker-tmp-dir /dev/shm \
         --timeout ${GUNICORN_TIMEOUT:-30} \
         --workers ${GUNICORN_WORKERS:-3} \
         --threads ${GUNICORN_THREADS:-2} \
         --access-logfile $ACCESS_LOG_LOCATION \
         app.wsgi
