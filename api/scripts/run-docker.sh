#!/bin/bash
set -e

# The script can take 2 optional arguments:
# 1. The django target to run
# 2. For migrate, serve and migrate-and-serve, the number of seconds to sleep before running

function migrate () {
    python manage.py waitfordb && python manage.py migrate && python manage.py createcachetable
}
function serve() {
    # configuration parameters for statsd. Docs can be found here:
    # https://docs.gunicorn.org/en/stable/instrumentation.html
    export STATSD_PORT=${STATSD_PORT:-8125}
    export STATSD_PREFIX=${STATSD_PREFIX:-flagsmith.api}

    python manage.py waitfordb

    exec gunicorn --bind 0.0.0.0:8000 \
             --worker-tmp-dir /dev/shm \
             --timeout ${GUNICORN_TIMEOUT:-30} \
             --workers ${GUNICORN_WORKERS:-3} \
             --threads ${GUNICORN_THREADS:-2} \
             --access-logfile $ACCESS_LOG_LOCATION \
             --logger-class ${GUNICORN_LOGGER_CLASS:-'util.logging.GunicornJsonCapableLogger'} \
             --access-logformat ${ACCESS_LOG_FORMAT:-'%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %({origin}i)s %({access-control-allow-origin}o)s'} \
             --keep-alive ${GUNICORN_KEEP_ALIVE:-2} \
             ${STATSD_HOST:+--statsd-host $STATSD_HOST:$STATSD_PORT} \
             ${STATSD_HOST:+--statsd-prefix $STATSD_PREFIX} \
             app.wsgi
}
function run_task_processor() {
    python manage.py waitfordb --waitfor 30 --migrations
    if [[ -n "$ANALYTICS_DATABASE_URL" || -n "$DJANGO_DB_NAME_ANALYTICS" ]]; then
        python manage.py waitfordb --waitfor 30 --migrations --database analytics
    fi
    RUN_BY_PROCESSOR=1 exec python manage.py runprocessor \
      --sleepintervalms ${TASK_PROCESSOR_SLEEP_INTERVAL:-500} \
      --graceperiodms ${TASK_PROCESSOR_GRACE_PERIOD_MS:-20000} \
      --numthreads ${TASK_PROCESSOR_NUM_THREADS:-5} \
      --queuepopsize ${TASK_PROCESSOR_QUEUE_POP_SIZE:-10}
}
function migrate_identities(){
    python manage.py migrate_to_edge "$1"
}
function migrate_analytics_db(){
    # if `$ANALYTICS_DATABASE_URL` or DJANGO_DB_NAME_ANALYTICS is set
    # run the migration command
    if [[ -z "$ANALYTICS_DATABASE_URL" && -z "$DJANGO_DB_NAME_ANALYTICS" ]]; then
        return 0
    fi
    python manage.py migrate --database analytics
}
function import_organisation_from_s3(){
    python manage.py importorganisationfroms3 "$1" "$2"
}
function dump_organisation_to_s3(){
    python manage.py dumporganisationtos3 "$1" "$2" "$3"
}
function dump_organisation_to_local_fs(){
    python manage.py dumporganisationtolocalfs "$1" "$2"
}
function bootstrap(){
    python manage.py bootstrap
}
# Note: `go_to_sleep` is deprecated and will be removed in a future release.
function go_to_sleep(){
    echo "Sleeping for ${1} seconds before startup"
    sleep ${1}
}

if [ "$1" == "migrate" ]; then
    if [ $# -eq 2 ]; then go_to_sleep "$2"; fi
    migrate
    migrate_analytics_db
elif [ "$1" == "serve" ]; then
    if [ $# -eq 2 ]; then go_to_sleep "$2"; fi
    serve
elif [ "$1" == "run-task-processor" ]; then
    run_task_processor
elif [ "$1" == "migrate-and-serve" ]; then
    if [ $# -eq 2 ]; then go_to_sleep "$2"; fi
    migrate
    migrate_analytics_db
    bootstrap
    serve
elif [ "$1" == "migrate-identities" ]; then
    migrate_identities "$2"
elif [ "$1" == "import-organisation-from-s3" ]; then
    import_organisation_from_s3 "$2" "$3"
elif [ "$1" == "dump-organisation-to-s3" ]; then
    dump_organisation_to_s3 "$2" "$3" "$4"
elif [ "$1" == "dump-organisation-to-local-fs" ]; then
    dump_organisation_to_local_fs "$2" "$3"
else
   echo "ERROR: unrecognised command '$1'"
fi
