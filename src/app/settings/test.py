from app.settings.common import *
import os

from app.utils import parse_database_url

DATABASES['default'] = parse_database_url(os.environ['DATABASE_URL'])
