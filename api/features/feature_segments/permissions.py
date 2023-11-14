from contextlib import suppress

from rest_framework.permissions import IsAuthenticated

from environments.models import Environment
from environments.permissions.constants import MANAGE_SEGMENT_OVERRIDES


class FeatureSegmentPermissions(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        # detail view means we can just defer to object permissions
        if view.detail:
            return True

        # handle by the view
        if view.action in ["list", "get_by_uuid", "update_priorities"]:
            return True

        if view.action == "create":
            with suppress(Environment.DoesNotExist, ValueError):
                environment = request.data.get("environment")
                environment = Environment.objects.get(id=int(environment))

                return request.user.has_environment_permission(
                    MANAGE_SEGMENT_OVERRIDES, environment
                )

        return False

    def has_object_permission(self, request, view, obj):
        return request.user.has_environment_permission(
            MANAGE_SEGMENT_OVERRIDES, environment=obj.environment
        )
