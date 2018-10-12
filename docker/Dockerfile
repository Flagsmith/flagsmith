FROM python:2.7

RUN rm /var/lib/dpkg/info/format
RUN printf "1\n" > /var/lib/dpkg/info/format
RUN dpkg --configure -a
RUN  apt-get clean && apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pipenv

WORKDIR /usr/src/app
COPY Pipfile* ./
RUN pipenv install --deploy

ENV DJANGO_SETTINGS_MODULE=app.settings.master-docker

EXPOSE 8000
