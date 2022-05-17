from django.utils.decorators import method_decorator
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from audit.models import (
    SEGMENT_FEATURE_STATE_DELETED_MESSAGE,
    AuditLog,
    RelatedObjectType,
)
from features.feature_segments.serializers import (
    FeatureSegmentChangePrioritiesSerializer,
    FeatureSegmentCreateSerializer,
    FeatureSegmentListSerializer,
    FeatureSegmentQuerySerializer,
)
from features.models import FeatureSegment


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(query_serializer=FeatureSegmentQuerySerializer()),
)
@method_decorator(
    name="update_priorities",
    decorator=swagger_auto_schema(
        responses={200: FeatureSegmentListSerializer(many=True)}
    ),
)
class FeatureSegmentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    def get_queryset(self):
        permitted_projects = self.request.user.get_permitted_projects(["VIEW_PROJECT"])
        queryset = FeatureSegment.objects.filter(
            feature__project__in=permitted_projects
        )

        if self.action == "list":
            filter_serializer = FeatureSegmentQuerySerializer(
                data=self.request.query_params
            )
            filter_serializer.is_valid(raise_exception=True)
            return queryset.filter(**filter_serializer.data)

        return queryset

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return FeatureSegmentCreateSerializer

        if self.action == "update_priorities":
            return FeatureSegmentChangePrioritiesSerializer

        return FeatureSegmentListSerializer

    def get_serializer(self, *args, **kwargs):
        if self.action == "update_priorities":
            # update the serializer kwargs to ensure docs here are correct
            kwargs = {**kwargs, "many": True, "partial": True}
        return super(FeatureSegmentViewSet, self).get_serializer(*args, **kwargs)

    def perform_destroy(self, instance):
        # feature state <-> feature segment relationship is incorrectly modelled as a
        # foreign key instead of one to one, so we need to grab the first feature state
        feature_state = instance.feature_states.first()
        message = SEGMENT_FEATURE_STATE_DELETED_MESSAGE % (
            instance.feature.name,
            instance.segment.name,
        )
        audit_log_record = (
            AuditLog.create_record(
                obj=feature_state,
                obj_type=RelatedObjectType.FEATURE_STATE,
                log_message=message,
                author=self.request.user,
                project=instance.feature.project,
                environment=instance.environment,
                persist=False,
            )
            if feature_state
            else None
        )

        instance.delete()

        if audit_log_record:
            audit_log_record.save()

    @action(detail=False, methods=["POST"], url_path="update-priorities")
    def update_priorities(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_instances = serializer.save()
        return Response(
            FeatureSegmentListSerializer(instance=updated_instances, many=True).data
        )
