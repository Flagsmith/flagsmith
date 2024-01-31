from django.db import models

from projects.models import Project


class ExternalResources(models.Model):
    url = models.URLField()
    type = models.TextField()
    resources_id = models.TextField(null=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="external_resource",
    )
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
