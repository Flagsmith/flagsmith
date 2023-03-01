from core.models import AbstractBaseExportableModel, SoftDeleteExportableModel
from django.db import models


class AbstractBaseWebhookModel(models.Model):
    url = models.URLField()
    secret = models.CharField(max_length=255, blank=True)

    class Meta:
        abstract = True


class AbstractBaseExportableWebhookModel(
    AbstractBaseWebhookModel, AbstractBaseExportableModel
):
    class Meta:
        abstract = True


class AbstractBaseSoftDeleteExportableWebhookModel(
    AbstractBaseWebhookModel, SoftDeleteExportableModel
):
    class Meta:
        abstract = True
