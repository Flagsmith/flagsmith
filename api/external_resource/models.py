from django.db import models


class ExternalResource(models.Model):
    url = models.URLField()
    type = models.TextField()
    feature_external_resource = models.ManyToManyField(
        to="features.Feature", blank=True, through="FeatureExternalResource"
    )

    class Meta:
        ordering = ["id"]


class FeatureExternalResource(models.Model):
    external_resource = models.ForeignKey(ExternalResource, on_delete=models.CASCADE)
    feature = models.ForeignKey(
        "features.feature",
        on_delete=models.CASCADE,
        related_name="FeatureExternalResource",
    )

    class Meta:
        ordering = ("id",)
