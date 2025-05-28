from common.environments.permissions import (
    MANAGE_SEGMENT_OVERRIDES,
)
from rest_framework.permissions import IsAuthenticated

from environments.models import Environment


class FeatureSegmentPermissions(IsAuthenticated):
    def has_permission(self, request, view):  # type: ignore[no-untyped-def]
        if not super().has_permission(request, view):
            return False

        # detail view means we can just defer to object permissions
        if view.detail:
            return True

        # handle by the view
        if view.action in ["list", "get_by_uuid", "update_priorities"]:
            return True

        if view.action == "create":
            if not (environment_pk := request.data.get("environment")):
                return False

            try:
                environment = Environment.objects.get(pk=environment_pk)
            except Environment.DoesNotExist:
                return False

            return request.user.has_environment_permission(
                MANAGE_SEGMENT_OVERRIDES, environment
            )

        return False

    def has_object_permission(self, request, view, obj):  # type: ignore[no-untyped-def]
        return request.user.has_environment_permission(
            MANAGE_SEGMENT_OVERRIDES, environment=obj.environment
        )
