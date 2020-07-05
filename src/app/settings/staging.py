from app.settings.common import *
import os

from app.utils import parse_database_url

DATABASES['default'] = parse_database_url(os.environ['DATABASE_URL'])

DEBUG = False

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'INFO'
        },
        'gunicorn': {
            'handlers': ['console'],
            'level': 'DEBUG'
        }
    }
}

REST_FRAMEWORK['PAGE_SIZE'] = 999

SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [r'^/$', r'^$']  # root is exempt as it's used for EB health checks
