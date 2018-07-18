from app.settings.common import *
import os

import dj_database_url

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
        }
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
