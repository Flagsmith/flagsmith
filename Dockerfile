FROM python:3.8 as build

#RUN rm /var/lib/dpkg/info/format
#RUN printf "1\n" > /var/lib/dpkg/info/format
#RUN dpkg --configure -a
#RUN  apt-get clean && apt-get update \
#    && apt-get install -y --no-install-recommends \
#        postgresql-client \
#    && rm -rf /var/lib/apt/lists/* \
#    && apt-get purge -y --auto-remove gcc 
    
RUN pip install pipenv

WORKDIR /app
COPY Pipfile Pipfile.lock /app/
RUN bash -c 'PIPENV_VENV_IN_PROJECT=1 pipenv install'


FROM python:3.8-slim as application

WORKDIR /app
COPY --from=build /app /app/

COPY src/ /app/src/
COPY bin/ /app/bin/
COPY Pipfile* /app/

ENV DJANGO_SETTINGS_MODULE=app.settings.master-docker
EXPOSE 8000

CMD ["./bin/docker"]
