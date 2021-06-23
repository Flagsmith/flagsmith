#!/bin/bash
set -e

python manage.py migrate
python manage.py collectstatic --no-input
python manage.py runserver 0.0.0.0:8000
