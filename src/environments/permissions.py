from rest_framework import exceptions
from rest_framework.permissions import BasePermission


class EnvironmentKeyPermissions(BasePermission):
    def has_permission(self, request, view):
        # Authentication class will set the environment on the request if it exists
        if hasattr(request, 'environment'):
            return True

        raise exceptions.PermissionDenied('Missing or invalid Environment Key')

    def has_object_permission(self, request, view, obj):
        """
        This method is only called if has_permission returns true so we can safely return true for all requests here.
        """
        return True
