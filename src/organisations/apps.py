# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class OrganisationsConfig(AppConfig):
    name = 'organisations'

    def ready(self):
        # noinspection PyUnresolvedReferences
        import organisations.signals
