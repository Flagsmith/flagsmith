FROM registry.redhat.io/ubi8/python-38 as application

MAINTAINER Ben Rometsch <support@flagsmith.com>

LABEL name="flagsmith-api" \
      vendor="Flagsmith" \
      maintainer="support@flagsmith.com" \
      version="0.0.1" \
      summary="Feature Flags and Remote Config API" \
      description="Feature Flags and Remote Config API"
COPY License /licenses/License

USER root
RUN yum -y update-minimal --security --sec-severity=Important --sec-severity=Critical
USER 1001

ADD --chown=1001:0 requirements.txt .
RUN pip install -r requirements.txt
ADD --chown=1001:0 docker/ bin/
ADD --chown=1001:0 . src/

RUN python src/manage.py collectstatic --no-input

ARG ACCESS_LOG_LOCATION="/dev/null"
ENV ACCESS_LOG_LOCATION=${ACCESS_LOG_LOCATION}
ENV DJANGO_SETTINGS_MODULE=app.settings.production

EXPOSE 8000

CMD ["./bin/docker"]
