from django.db import models
from rest_framework_api_key.models import AbstractAPIKey

from organisations.models import Organisation


class MasterAPIKey(AbstractAPIKey):
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="master_api_keys",
    )
