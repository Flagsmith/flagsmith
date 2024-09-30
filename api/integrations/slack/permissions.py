from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from environments.models import Environment


class OauthInitPermission(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        environment = Environment.objects.get(
            api_key=view.kwargs.get("environment_api_key")
        )
        return request.user.is_environment_admin(environment)


class SlackGetChannelPermissions(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        environment = get_object_or_404(
            Environment.objects.select_related("project"),
            api_key=view.kwargs.get("environment_api_key"),
        )
        return request.user.is_project_admin(environment.project)
