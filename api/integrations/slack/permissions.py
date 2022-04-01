import logging

from rest_framework.permissions import BasePermission

from environments.models import Environment

logger = logging.getLogger(__name__)


class OauthInitPermission(BasePermission):
    def has_permission(self, request, view):

        logger.error(
            "OauthInitPermission called with user: %s and view: %s", request.user, view
        )
        environment = Environment.objects.get(
            api_key=view.kwargs.get("environment_api_key")
        )
        return request.user.is_environment_admin(environment)
