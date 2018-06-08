from common import *
import os


ALLOWED_HOSTS.extend(['.ngrok.io', '127.0.0.1', 'localhost'])

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

BASE_URL = "http://localhost:8000"
