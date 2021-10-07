from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase

from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from organisations.models import Organisation
from projects.models import Project
from projects.tags.models import Tag
from segments.models import Segment

from .helpers import *


class TimeSuite:
    """
    An example benchmark that times the performance of various kinds
    of iterating over dictionaries in Python.
    """

    def setup(self):
        self.organisation = Organisation.objects.create(name="Test Org 222")

    def time_keys(self):
        pass
