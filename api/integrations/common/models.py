from core.models import AbstractBaseExportableModel
from django.db import models


class IntegrationsModel(AbstractBaseExportableModel):
    base_url = models.URLField(blank=False, null=True)
    api_key = models.CharField(max_length=100, blank=False, null=False)

    class Meta:
        abstract = True
