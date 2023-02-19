from django.db import models
from rest_framework_api_key.models import AbstractAPIKey
from softdelete.models import SoftDeleteObject

from organisations.models import Organisation


class MasterAPIKey(AbstractAPIKey, SoftDeleteObject):
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="master_api_keys",
    )
