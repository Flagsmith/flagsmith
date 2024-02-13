from django.db import models
from rest_framework_api_key.models import AbstractAPIKey, APIKeyManager
from softdelete.models import SoftDeleteManager, SoftDeleteObject

from organisations.models import Organisation


class MasterAPIKeyManager(APIKeyManager, SoftDeleteManager):
    pass


class MasterAPIKey(AbstractAPIKey, SoftDeleteObject):
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="master_api_keys",
    )

    objects = MasterAPIKeyManager()
    is_admin = models.BooleanField(default=True)
