import logging

from common.projects.permissions import VIEW_PROJECT
from django.db import transaction
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from environments.models import Environment
from features.dependencies.services import validate_segment_flag_dependencies
from features.feature_segments.serializers import (
    FeatureSegmentChangePrioritiesSerializer,
    FeatureSegmentCreateSerializer,
    FeatureSegmentListSerializer,
    FeatureSegmentQuerySerializer,
)
from features.feature_segments.services import (
    create_priorities_changed_audit_log,
    get_reordered_priorities,
)
from features.future.services import (
    delete_segment_override,
    get_next_segment_override_priority,
    get_segment_override,
    get_segment_overrides,
    is_live_segment_override,
    update_flag,
)
from features.models import FeatureSegment
from features.versioning.versioning_service import (
    get_current_live_environment_feature_version,
)
from segments.services import check_segment_is_not_system

from .permissions import FeatureSegmentPermissions

logger = logging.getLogger(__name__)


@method_decorator(
    name="list",
    decorator=extend_schema(
        tags=["mcp"],
        parameters=[FeatureSegmentQuerySerializer],
        operation_id="list_feature_segments",
        description="Lists segment overrides for a feature in an environment.",
    ),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(
        tags=["mcp"],
        operation_id="delete_feature_segment",
        description="Deletes a segment override. Applies to environments without v2 feature versioning (use_v2_feature_versioning: false).",
    ),
)
class FeatureSegmentViewSet(
    viewsets.ModelViewSet,  # type: ignore[type-arg]
):
    permission_classes = [FeatureSegmentPermissions]

    def get_queryset(self):  # type: ignore[no-untyped-def]
        if getattr(self, "swagger_fake_view", False):
            return FeatureSegment.objects.none()

        permitted_projects = self.request.user.get_permitted_projects(  # type: ignore[union-attr]
            permission_key=VIEW_PROJECT
        )

        queryset = FeatureSegment.objects.filter(
            feature__project__in=permitted_projects
        )

        if self.action == "list":
            filter_serializer = FeatureSegmentQuerySerializer(
                data=self.request.query_params
            )
            filter_serializer.is_valid(raise_exception=True)

            environment_id = filter_serializer.validated_data["environment"]
            environment = Environment.objects.get(id=environment_id)
            if environment.use_v2_feature_versioning:
                queryset = queryset.filter(
                    environment_feature_version=get_current_live_environment_feature_version(
                        environment_id=environment_id,
                        feature_id=filter_serializer.validated_data["feature"],
                    )
                )

            return queryset.select_related("segment").filter(**filter_serializer.data)

        return queryset

    def perform_create(self, serializer: BaseSerializer[FeatureSegment]) -> None:
        environment = serializer.validated_data["environment"]
        feature = serializer.validated_data["feature"]
        segment = serializer.validated_data["segment"]
        if environment.use_v2_feature_versioning:
            # Overrides of v2 environments are drafted for their feature states
            # to be added to versions, rather than going live.
            # TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
            check_segment_is_not_system(segment)
            with transaction.atomic():
                feature_segment = serializer.save()
                validate_segment_flag_dependencies(feature_segment.segment)
            return
        if get_segment_override(
            environment=environment, feature=feature, segment_id=segment.id
        ):
            raise ValidationError("The flag is already overridden for this segment.")
        # Serves the environment default until the override's state is set.
        update_flag(
            environment=environment,
            feature=feature,
            changes={
                "segment_overrides": [
                    {
                        "segment": {"id": segment.id},
                        "priority": get_next_segment_override_priority(
                            environment=environment, feature=feature
                        ),
                    }
                ]
            },
            replace=False,
            author=self.request.user,  # type: ignore[arg-type]
            system=False,
        )
        override = get_segment_override(
            environment=environment, feature=feature, segment_id=segment.id
        )
        serializer.instance = override.feature_segment  # type: ignore[union-attr]

    @transaction.atomic
    def perform_update(self, serializer: BaseSerializer[FeatureSegment]) -> None:
        # TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
        check_segment_is_not_system(serializer.instance.segment)  # type: ignore[union-attr]
        if segment := serializer.validated_data.get("segment"):
            check_segment_is_not_system(segment)
        feature_segment = serializer.save()
        validate_segment_flag_dependencies(feature_segment.segment)

    def perform_destroy(self, instance: FeatureSegment) -> None:
        if is_live_segment_override(instance):
            delete_segment_override(
                environment=instance.environment,
                feature=instance.feature,
                segment_id=instance.segment_id,
                author=self.request.user,  # type: ignore[arg-type]
                system=False,
            )
            return
        # TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
        check_segment_is_not_system(instance.segment)
        instance.delete()

    def get_serializer_class(self):  # type: ignore[no-untyped-def]
        if self.action in ["create", "update", "partial_update"]:
            return FeatureSegmentCreateSerializer

        if self.action == "update_priorities":
            return FeatureSegmentChangePrioritiesSerializer

        return FeatureSegmentListSerializer

    @extend_schema(
        request=FeatureSegmentChangePrioritiesSerializer(many=True),
        responses={200: FeatureSegmentListSerializer(many=True)},
    )
    @action(detail=False, methods=["POST"], url_path="update-priorities")
    def update_priorities(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        if not (
            new_priorities := {
                item["id"]: item["priority"] for item in serializer.validated_data
            }
        ):
            return Response([])

        reordered = list(
            FeatureSegment.objects.filter(id__in=new_priorities).select_related(
                "environment", "feature", "segment"
            )
        )
        environment = reordered[0].environment
        feature = reordered[0].feature
        feature_segments = list(
            FeatureSegment.objects.filter(
                environment=environment,
                feature=feature,
                environment_feature_version=reordered[0].environment_feature_version,
            ).select_related("segment")
        )
        priorities = get_reordered_priorities(feature_segments, new_priorities)
        moved = [
            feature_segment
            for feature_segment in feature_segments
            if priorities[feature_segment.id] != feature_segment.priority
        ]
        if not moved:
            return Response(
                FeatureSegmentListSerializer(instance=reordered, many=True).data
            )

        live_feature_segment_ids = {
            override.feature_segment_id
            for override in get_segment_overrides(
                environment=environment, feature=feature
            ).values()
        }
        if any(
            feature_segment.id not in live_feature_segment_ids
            for feature_segment in feature_segments
        ):
            # TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
            for feature_segment in moved:
                check_segment_is_not_system(feature_segment.segment)
            return Response(
                FeatureSegmentListSerializer(instance=serializer.save(), many=True).data
            )

        previous_priorities = [
            (feature_segment.id, feature_segment.priority)
            for feature_segment in reordered
        ]
        update_flag(
            environment=environment,
            feature=feature,
            changes={
                "segment_overrides": [
                    {
                        "segment": {"id": feature_segment.segment_id},
                        "priority": priorities[feature_segment.id],
                    }
                    for feature_segment in moved
                ]
            },
            replace=False,
            author=request.user,
            system=False,
        )
        create_priorities_changed_audit_log(
            request,
            previous_priorities=previous_priorities,
            feature_segment_ids=list(new_priorities),
        )
        # Overrides of v2 environments are now in a new version.
        overrides = get_segment_overrides(environment=environment, feature=feature)
        return Response(
            FeatureSegmentListSerializer(
                instance=[
                    overrides[feature_segment.segment_id].feature_segment
                    for feature_segment in reordered
                ],
                many=True,
            ).data
        )

    @action(
        detail=False,
        url_path=r"get-by-uuid/(?P<uuid>[0-9a-f-]+)",
        methods=["get"],
    )
    def get_by_uuid(self, request, uuid):  # type: ignore[no-untyped-def]
        qs = self.get_queryset()  # type: ignore[no-untyped-call]
        feature_segment = get_object_or_404(qs, uuid=uuid)
        serializer = self.get_serializer(feature_segment)
        return Response(serializer.data)
