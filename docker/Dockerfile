FROM python:3.8-slim as application

WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY docker/bin/ /app/bin/
COPY src/ /app/src/

RUN python src/manage.py collectstatic --no-input

ENV DJANGO_SETTINGS_MODULE=app.settings.production
EXPOSE 8000

CMD ["./bin/docker"]
