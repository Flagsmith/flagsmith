import os
import sys
from contextlib import contextmanager
from functools import wraps
from os.path import dirname

import django
from django.utils.timezone import now

from organisations.models import Organisation

os.environ["DJANGO_SETTINGS_MODULE"] = "app.settings.local"
sys.path.append(dirname(dirname(__file__)))


django.setup()


organisation = Organisation.objects.create(name="Test Org 222")
