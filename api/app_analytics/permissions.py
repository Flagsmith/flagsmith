from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from organisations.models import Organisation


class UsageDataPermission(BasePermission):
    def has_permission(self, request, view):
        organisation_pk = view.kwargs.get("organisation_pk")
        if organisation_pk and request.user.is_organisation_admin(
            Organisation.objects.get(pk=organisation_pk)
        ):
            return True

        raise PermissionDenied(
            "User does not have sufficient privileges to perform this action"
        )

    def has_object_permission(self, request, view, obj):
        # Object level permissions are not required for the usage data API
        raise NotImplementedError()
