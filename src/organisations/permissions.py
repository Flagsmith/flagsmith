from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


class OrganisationPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.action in ('users', 'remove_users') and not request.user.is_admin(obj):
            raise PermissionDenied('User does not have sufficient privileges to perform this action')