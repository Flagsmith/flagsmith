import logging

from rest_framework.permissions import IsAuthenticated

from environments.models import Environment

logger = logging.getLogger(__name__)


class OauthInitPermission(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        logger.debug(
            "OauthInitPermission called with user: %s and view: %s", request.user, view
        )
        environment = Environment.objects.get(
            api_key=view.kwargs.get("environment_api_key")
        )
        return request.user.is_environment_admin(environment)
