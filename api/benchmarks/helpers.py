import os
import sys
from contextlib import contextmanager
from functools import wraps
from os.path import dirname

import django
from django.utils.timezone import now

os.environ["DJANGO_SETTINGS_MODULE"] = "app.settings.local"
os.environ["DJANGO_ALLOWED_HOSTS"] = "*"
os.environ["DEBUG"] = "False"
os.environ["INFLUXDB_TOKEN"] = ""
sys.path.append(dirname(dirname(__file__)))


django.setup()
