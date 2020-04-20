from app.settings.common import *
import os

import dj_database_url

DATABASES['default'] = dj_database_url.parse(os.environ['DATABASE_URL'], conn_max_age=60)

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

STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = 'bullet-train-api-staging'
AWS_LOCATION = 'static'
AWS_S3_REGION_NAME = 'eu-west-2'
AWS_DEFAULT_ACL = 'public-read'
AWS_S3_ADDRESSING_STYLE = 'virtual'
