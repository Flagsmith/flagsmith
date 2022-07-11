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
             --keep-alive ${GUNICORN_KEEP_ALIVE:-2} \
             app.wsgi
}
function migrate_identities(){
    python manage.py migrate_to_edge "$1"
}
function import_organisation(){
    python manage.py importorganisation "$1" "$2"
}

if [ "$1" == "migrate" ]; then
    migrate
elif [ "$1" == "serve" ]; then
    serve
elif [ "$1" == "migrate_identities" ]; then
    migrate_identities $2
elif [ "$1" == "import-organisation" ]; then
    import_organisation $2 $3
elif [ "$1" == "migrate-and-serve" ]; then
    migrate
    serve
fi
