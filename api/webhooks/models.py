from django.db import models

from core.fields import NoSSRFURLField
from core.models import AbstractBaseExportableModel, SoftDeleteExportableModel


class AbstractBaseWebhookModel(models.Model):
    url = NoSSRFURLField(max_length=200)
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
