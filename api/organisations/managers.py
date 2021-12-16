from django.db.models import Manager

from permissions.models import ORGANISATION_PERMISSION_TYPE


class OrganisationPermissionManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(type=ORGANISATION_PERMISSION_TYPE)
