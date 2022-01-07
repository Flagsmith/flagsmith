from django.db import models


class AbstractBaseWebhookModel(models.Model):
    url = models.URLField()
    secret = models.CharField(max_length=255, blank=True)

    class Meta:
        abstract = True
