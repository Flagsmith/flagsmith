#!/bin/bash
set -e

python manage.py migrate
gunicorn --bind 0.0.0.0:8000 --worker-tmp-dir /dev/shm --workers ${GUNICORN_WORKERS:-3} --threads ${GUNICORN_THREADS:-2} app.wsgi --access-logfile $ACCESS_LOG_LOCATION
