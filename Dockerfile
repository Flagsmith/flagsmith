FROM python:3.8
ENV PYTHONUNBUFFERED 1

RUN rm /var/lib/dpkg/info/format
RUN printf "1\n" > /var/lib/dpkg/info/format
RUN dpkg --configure -a
RUN  apt-get clean && apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove gcc 
    
RUN pip install pipenv
RUN mkdir /app
WORKDIR /app

COPY src/ /app/
COPY bin/ /app/bin/
COPY Pipfile* /app/

RUN pipenv install
ENV DJANGO_SETTINGS_MODULE=app.settings.master-docker
EXPOSE 8000

CMD ["./bin/docker"]
