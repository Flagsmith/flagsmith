import logging

from core.permissions import HasMasterAPIKey
from django.utils.decorators import method_decorator
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from features.feature_segments.serializers import (
    FeatureSegmentChangePrioritiesSerializer,
    FeatureSegmentCreateSerializer,
    FeatureSegmentListSerializer,
    FeatureSegmentQuerySerializer,
)
from features.models import FeatureSegment
from projects.models import Project

logger = logging.getLogger(__name__)


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
    viewsets.ModelViewSet,
):
    permission_classes = [IsAuthenticated | HasMasterAPIKey]

    def get_queryset(self):
        if hasattr(self.request, "master_api_key"):
            permitted_projects = Project.objects.filter(
                organisation_id=self.request.master_api_key.organisation_id
            )
        else:
            permitted_projects = self.request.user.get_permitted_projects(
                permissions=["VIEW_PROJECT"]
            )
        queryset = FeatureSegment.objects.filter(
            feature__project__in=permitted_projects
        )

        if self.action == "list":
            filter_serializer = FeatureSegmentQuerySerializer(
                data=self.request.query_params
            )
            filter_serializer.is_valid(raise_exception=True)
            return queryset.select_related("segment").filter(**filter_serializer.data)

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

    @action(detail=False, methods=["POST"], url_path="update-priorities")
    def update_priorities(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_instances = serializer.save()
        return Response(
            FeatureSegmentListSerializer(instance=updated_instances, many=True).data
        )

    @action(
        detail=False,
        url_path=r"get-by-uuid/(?P<uuid>[0-9a-f-]+)",
        methods=["get"],
    )
    def get_by_uuid(self, request, uuid):
        qs = self.get_queryset()
        feature_segment = get_object_or_404(qs, uuid=uuid)
        serializer = self.get_serializer(feature_segment)
        return Response(serializer.data)
