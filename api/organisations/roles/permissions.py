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
                if role.organisation.id == int(view.kwargs.get("organisation_pk")):
                    if view.action == "create":
                        return True
                    return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_organisation_admin(obj.role.organisation):
            return True
        return False
