import os

accesslog = os.getenv("ACCESS_LOG_LOCATION")
access_log_format = os.getenv("ACCESS_LOG_FORMAT") or (
    r'%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" '
    r'"%(a)s" %({origin}i)s %({access-control-allow-origin}o)s'
)
keep_alive = os.getenv("GUNICORN_KEEP_ALIVE", 2)
logger_class = "util.logging.GunicornJsonLogger"
threads = os.getenv("GUNICORN_THREADS", 2)
timeout = os.getenv("GUNICORN_TIMEOUT", 30)
workers = os.getenv("GUNICORN_WORKERS", 3)

if _statsd_host := os.getenv("STATSD_HOST"):
    statsd_host = f'{_statsd_host}:{os.getenv("STATSD_PORT")}'
    statsd_prefix = os.getenv("STATSD_PREFIX")
