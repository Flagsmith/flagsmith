FROM python:3.8-slim as application

WORKDIR /app
COPY requirements.txt /app/
COPY src/ /app/src/
COPY bin/ /app/bin/

RUN pip install -r requirements.txt

ENV DJANGO_SETTINGS_MODULE=app.settings.master-docker
EXPOSE 8000

CMD ["./bin/docker"]
