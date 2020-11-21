import os

import dj_database_url

from app.settings.common import *

DATABASES["default"] = dj_database_url.parse(os.environ["DATABASE_URL"])
