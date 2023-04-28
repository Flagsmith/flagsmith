from contextlib import suppress

from django.core.exceptions import ObjectDoesNotExist

from organisations.permissions.permissions import (
    NestedIsOrganisationAdminPermission,
)
from organisations.roles.models import Role


class NestedRolePermission(NestedIsOrganisationAdminPermission):
    def has_permission(self, request, view):
        if super().has_permission(request, view):
            roles_pk = view.kwargs.get("role_pk")
            with suppress(ObjectDoesNotExist):
                role = Role.objects.get(pk=roles_pk)
                # Check if the role belongs to the organisation
                # Note: user is already checked to be an admin of the organisation(using parent class)
                return role.organisation.id == int(view.kwargs.get("organisation_pk"))
        return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_organisation_admin(obj.role.organisation):
            return True
        return False
