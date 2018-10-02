from app.settings.common import *
import os


ALLOWED_HOSTS.extend(['.ngrok.io', '127.0.0.1', 'localhost'])

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'bullettrain',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': '127.0.0.1',
        'PORT': 5432
    }
}
