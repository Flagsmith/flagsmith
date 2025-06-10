import sentry_sdk
from django.apps import AppConfig
from django.conf import settings
from sentry_sdk.integrations.django import DjangoIntegration

from .samplers import traces_sampler


class SentryConfig(AppConfig):
    name = "integrations.sentry"

    def ready(self):  # type: ignore[no-untyped-def]
        if settings.SENTRY_SDK_DSN:
            sentry_sdk.init(
                dsn=settings.SENTRY_SDK_DSN,
                integrations=[DjangoIntegration()],
                environment=settings.ENV,
                traces_sampler=traces_sampler,
                # If you wish to associate users to errors (assuming you are using
                # django.contrib.auth) you may enable sending PII data.
                send_default_pii=True,
            )
