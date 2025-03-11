# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from core.apps import BaseAppConfig


class FeaturesConfig(BaseAppConfig):
    name = "features"
    default = True

    def ready(self):  # type: ignore[no-untyped-def]
        super().ready()  # type: ignore[no-untyped-call]

        # noinspection PyUnresolvedReferences
        import features.signals  # noqa
