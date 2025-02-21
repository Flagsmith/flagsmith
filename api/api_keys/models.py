from django.conf import settings
from django.db import models
from django_lifecycle import (  # type: ignore[import-untyped]
    BEFORE_UPDATE,
    LifecycleModelMixin,
    hook,
)
from rest_framework_api_key.models import AbstractAPIKey, APIKeyManager
from softdelete.models import (  # type: ignore[import-untyped]
    SoftDeleteManager,
    SoftDeleteObject,
)

from organisations.models import Organisation


class MasterAPIKeyManager(APIKeyManager, SoftDeleteManager):  # type: ignore[misc]
    pass


class MasterAPIKey(AbstractAPIKey, LifecycleModelMixin, SoftDeleteObject):  # type: ignore[django-manager-missing,misc]  # noqa: E501  # noqa: E501
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="master_api_keys",
    )

    objects = MasterAPIKeyManager()  # type: ignore[misc]
    is_admin = models.BooleanField(default=True)

    @hook(BEFORE_UPDATE, when="is_admin", was=False, is_now=True)
    def delete_role_api_keys(  # type: ignore[no-untyped-def]
        self,
    ):
        if settings.IS_RBAC_INSTALLED:
            from rbac.models import MasterAPIKeyRole  # type: ignore[import-not-found]

            MasterAPIKeyRole.objects.filter(master_api_key=self.id).delete()
