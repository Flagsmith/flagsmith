#!/bin/bash
set -e

python manage.py migrate
mkdir gunicorn-worker-tmp-dir
gunicorn --bind 0.0.0.0:8000 --worker-tmp-dir=gunicorn-worker-tmp-dir --workers ${GUNICORN_WORKERS:-3} --threads ${GUNICORN_THREADS:-2} --access-logfile $ACCESS_LOG_LOCATION app.wsgi
