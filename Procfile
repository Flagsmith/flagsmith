release: python src/manage.py migrate
web: gunicorn --bind 0.0.0.0:${PORT:-8000} -w 3 --pythonpath src app.wsgi