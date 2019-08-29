from app.settings.common import *
import os

import dj_database_url

DATABASES['default'] = dj_database_url.parse(os.environ['DATABASE_URL'])