from django.db import models


class ExternalResources(models.Model):
    url = models.URLField()
    type = models.TextField()
    status = models.TextField(null=True)
    feature_external_resource = models.ManyToManyField(
        to="features.Feature", blank=True, through="FeatureExternalResources"
    )

    class Meta:
        ordering = ("id",)
        unique_together = ("url",)


class FeatureExternalResources(models.Model):
    feature = models.ForeignKey("features.Feature", on_delete=models.CASCADE)
    external_resource = models.ForeignKey(
        ExternalResources,
        on_delete=models.CASCADE,
        related_name="featureexternalresources",
    )

    class Meta:
        ordering = ("id",)
