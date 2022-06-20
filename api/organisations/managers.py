from django.db.models import Manager

from permissions.models import ORGANISATION_PERMISSION_TYPE


class OrganisationManager(Manager):
    def get_by_natural_key(self, *args):
        name, created_date = args
        return self.get(name=name, created_date=created_date)


class OrganisationPermissionManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(type=ORGANISATION_PERMISSION_TYPE)
