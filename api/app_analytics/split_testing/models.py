from django.db import models

from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature
from features.multivariate.models import MultivariateFeatureOption


class ConversionEventType(models.Model):
    name = models.CharField(max_length=100)
    environment = models.ForeignKey(
        Environment, related_name="conversion_event_types", on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(null=True, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["environment", "name"],
                name="unique_environment_name",
            )
        ]


class ConversionEvent(models.Model):
    type = models.ForeignKey(
        ConversionEventType, related_name="conversion_events", on_delete=models.CASCADE
    )
    environment = models.ForeignKey(
        Environment, related_name="conversion_events", on_delete=models.CASCADE
    )
    identity = models.ForeignKey(
        Identity,
        related_name="conversion_events",
        on_delete=models.CASCADE,
    )

    created_at = models.DateTimeField(null=True, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SplitTest(models.Model):
    conversion_event_type = models.ForeignKey(
        ConversionEventType, related_name="split_tests", on_delete=models.CASCADE
    )
    environment = models.ForeignKey(
        Environment, related_name="split_tests", on_delete=models.CASCADE
    )
    feature = models.ForeignKey(
        Feature, related_name="split_tests", on_delete=models.CASCADE
    )

    multivariate_feature_option = models.ForeignKey(
        MultivariateFeatureOption, on_delete=models.CASCADE, null=True
    )

    # Populated from the existing split testing tasks.py to the
    # number of unique identifiers for a single feature /
    # environment combination. Multiple occurences ignored.
    evaluation_count = models.PositiveIntegerField()
    # from the ConversionEvent model for matching identifiers.
    conversion_count = models.PositiveIntegerField()

    # The pvalue is the most useful split test metric for knowing
    # which of the candidates are statistically successful.
    # See the analyse_split_test helpers function for more details.
    pvalue = models.FloatField(null=False)

    created_at = models.DateTimeField(null=True, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "conversion_event_type",
                    "feature",
                    "multivariate_feature_option",
                ],
                name="unique_cet_feature_mvfo",
            )
        ]
