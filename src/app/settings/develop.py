from common import *
import os

import dj_database_url

ALLOWED_HOSTS = [os.environ['DJANGO_ALLOWED_HOST']]

DATABASES['default'] = dj_database_url.parse(os.environ['DATABASE_URL'])

DEBUG = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'app.handlers.MakeFileHandler',
            'filename': 'logs/django.log',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
