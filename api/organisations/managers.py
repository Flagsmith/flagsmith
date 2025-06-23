from django.db.models import Manager

from permissions.models import ORGANISATION_PERMISSION_TYPE


class OrganisationPermissionManager(Manager):  # type: ignore[type-arg]
    def get_queryset(self):  # type: ignore[no-untyped-def]
        return super().get_queryset().filter(type=ORGANISATION_PERMISSION_TYPE)
