from app.settings.common import *
import os


ALLOWED_HOSTS.extend(['.ngrok.io', '127.0.0.1', 'localhost'])

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DATABASE', 'bullettrain'),
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.environ['POSTGRES_PASSWORD'],
        'HOST': '127.0.0.1',
        'PORT': 5432
    }
}
