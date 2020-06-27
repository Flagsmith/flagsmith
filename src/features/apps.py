# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class FeaturesConfig(AppConfig):
    name = 'features'

    def ready(self):
        # noinspection PyUnresolvedReferences
        import features.signals
