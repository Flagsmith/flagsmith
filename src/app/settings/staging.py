from app.settings.common import *

# TODO: remove this in favour of production.py and environment variables

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "loggers": {
        "django": {"handlers": ["console"], "propagate": True, "level": "INFO"},
        "gunicorn": {"handlers": ["console"], "level": "DEBUG"},
    },
}

REST_FRAMEWORK["PAGE_SIZE"] = 999
