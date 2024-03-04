from django.db import models

from features.models import Feature


class ExternalResources(models.Model):
    url = models.URLField()
    type = models.TextField()
    status = models.TextField(null=True)
    feature = models.ForeignKey(
        Feature,
        related_name="features",
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ("id",)
        unique_together = ("url",)
