from django.core import validators
from django.db import models

from integrations.common.models import EnvironmentIntegrationModel


class SentryChangeTrackingConfiguration(EnvironmentIntegrationModel):
    """
    Integration with Sentry feature flags Change Tracking

    https://docs.sentry.io/product/issues/issue-details/feature-flags/#change-tracking
    """

    environment = models.OneToOneField(
        "environments.Environment",
        on_delete=models.CASCADE,
        related_name="sentry_change_tracking_configuration",
    )

    webhook_url = models.URLField(
        max_length=200,
    )

    # TODO: Persist hashed secret instead?
    secret = models.CharField(
        max_length=60,
        validators=[
            validators.MinLengthValidator(10),
        ],
    )
