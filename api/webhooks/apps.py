from django.apps import AppConfig


class WebhooksAppConfig(AppConfig):
    name = "webhooks"

    def ready(self) -> None:
        from django.db import models
        from rest_framework.serializers import ModelSerializer

        from webhooks.fields import NoSSRFURLField

        # Any `ModelSerializer` field built from a `models.URLField` gets the
        # SSRF-safe field instead, for every current and future serializer,
        # without each one having to opt in.
        ModelSerializer.serializer_field_mapping[models.URLField] = NoSSRFURLField
