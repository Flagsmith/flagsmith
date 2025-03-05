from contextlib import suppress

from common.environments.permissions import (  # type: ignore[import-untyped]
    MANAGE_SEGMENT_OVERRIDES,
)
from rest_framework.permissions import IsAuthenticated

from environments.models import Environment
from features.models import Feature


class FeatureSegmentPermissions(IsAuthenticated):
    def has_permission(self, request, view):  # type: ignore[no-untyped-def]
        if not super().has_permission(request, view):
            return False

        # detail view means we can just defer to object permissions
        if view.detail:
            return True

        # handled by the view
        if view.action in ["list", "get_by_uuid", "update_priorities"]:
            return True

        if view.action == "create":
            with suppress(Environment.DoesNotExist, ValueError):
                environment = request.data.get("environment")
                environment = Environment.objects.get(id=int(environment))

                feature_id = request.data.get("feature") or view.kwargs.get("feature_pk")
                feature = Feature.objects.get(
                    id=feature_id, project=environment.project
                )
                tag_ids = list(feature.tags.values_list("id", flat=True))

                return request.user.has_environment_permission(
                    permission=MANAGE_SEGMENT_OVERRIDES, environment=environment, tag_ids=tag_ids
                )

        return False

    def has_object_permission(self, request, view, obj):  # type: ignore[no-untyped-def]
        tag_ids = list(obj.feature.tags.values_list("id", flat=True))

        return request.user.has_environment_permission(
            permission=MANAGE_SEGMENT_OVERRIDES,
            environment=obj.environment,
            tag_ids=tag_ids,
        )
