release: python src/manage.py migrate
web: gunicorn --bind 0.0.0.0:${PORT:-8000} -w ${GUNICORN_WORKERS:-3} -w ${GUNICORN_THREADS:-2} --pythonpath src app.wsgi