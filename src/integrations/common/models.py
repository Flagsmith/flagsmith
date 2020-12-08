from django.db import models


class IntegrationsModel(models.Model):
    base_url = models.URLField(blank=False, null=False)
    api_key = models.CharField(max_length=100, blank=False, null=False)

    class Meta:
        abstract = True
