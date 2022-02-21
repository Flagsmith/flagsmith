#!/bin/bash
set -e

function migrate () {
    python manage.py migrate
}

function serve() {
    gunicorn --bind 0.0.0.0:8000 \
             --worker-tmp-dir /dev/shm \
             --timeout ${GUNICORN_TIMEOUT:-30} \
             --workers ${GUNICORN_WORKERS:-3} \
             --threads ${GUNICORN_THREADS:-2} \
             --access-logfile $ACCESS_LOG_LOCATION \
             app.wsgi
}
function migrate_project(){
    python manage.py migrate_to_edge $1
}
if [ "$1" == "migrate" ]; then
    migrate
elif [ "$1" == "serve" ]; then
    serve;
elif [ "$1" == "migrate_project" ]; then
    migrate_project $2;
elif [ "$1" == "migrate-and-serve" ]; then
    migrate
    serve
fi
