from django.conf import settings
from django.db import models
from django_lifecycle import BEFORE_UPDATE, LifecycleModelMixin, hook
from rest_framework_api_key.models import AbstractAPIKey, APIKeyManager
from softdelete.models import SoftDeleteManager, SoftDeleteObject

from organisations.models import Organisation


class MasterAPIKeyManager(APIKeyManager, SoftDeleteManager):
    pass


class MasterAPIKey(AbstractAPIKey, LifecycleModelMixin, SoftDeleteObject):
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="master_api_keys",
    )

    objects = MasterAPIKeyManager()
    is_admin = models.BooleanField(default=True)

    @hook(BEFORE_UPDATE, when="is_admin", was=False, is_now=True)
    def delete_role_api_keys(
        self,
    ):
        if settings.IS_RBAC_INSTALLED:
            from rbac.models import MasterAPIKeyRole

            MasterAPIKeyRole.objects.filter(master_api_key=self.id).delete()
