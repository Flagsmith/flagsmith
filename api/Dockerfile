FROM python:3.8-slim as application

WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY docker/ /app/bin/
COPY . /app/src/

RUN python src/manage.py collectstatic --no-input

ARG ACCESS_LOG_LOCATION="/dev/null"
ENV ACCESS_LOG_LOCATION=${ACCESS_LOG_LOCATION}

ENV DJANGO_SETTINGS_MODULE=app.settings.production
EXPOSE 8000

USER nobody

CMD ["./bin/docker"]
