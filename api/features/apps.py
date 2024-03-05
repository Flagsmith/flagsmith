# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from core.apps import BaseAppConfig


class FeaturesConfig(BaseAppConfig):
    name = "features"

    def ready(self):
        super().ready()

        # noinspection PyUnresolvedReferences
        import features.signals  # noqa
        import features.tasks  # noqa
