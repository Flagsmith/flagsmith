from common import *
import os

import dj_database_url

ALLOWED_HOSTS = [os.environ['DJANGO_ALLOWED_HOST']]

DATABASES['default'] = dj_database_url.parse(os.environ['DATABASE_URL'])

DEBUG = False

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'app.handlers.MakeFileHandler',
            'filename': 'logs/django.log',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
