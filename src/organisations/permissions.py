from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from organisations.models import Organisation


class NestedOrganisationEntityPermission(BasePermission):
    def has_permission(self, request, view):
        organisation_pk = view.kwargs.get('organisation_pk')
        if organisation_pk and request.user.is_admin(Organisation.objects.get(pk=organisation_pk)):
            return True

        raise PermissionDenied('User does not have sufficient privileges to perform this action')


class OrganisationPermission(BasePermission):
    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin(obj):
            return True

        raise PermissionDenied('User does not have sufficient privileges to perform this action')
