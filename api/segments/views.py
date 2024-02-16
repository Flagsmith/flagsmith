import logging

from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.decorators import action, api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from app.pagination import CustomPagination
from edge_api.identities.models import EdgeIdentity
from environments.identities.models import Identity
from features.models import FeatureState
from features.serializers import SegmentAssociatedFeatureStateSerializer
from projects.permissions import VIEW_PROJECT

from .models import Segment
from .permissions import SegmentPermissions
from .serializers import SegmentListQuerySerializer, SegmentSerializer

logger = logging.getLogger()


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(query_serializer=SegmentListQuerySerializer()),
)
class SegmentViewSet(viewsets.ModelViewSet):
    serializer_class = SegmentSerializer
    permission_classes = [SegmentPermissions]
    pagination_class = CustomPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Segment.objects.none()

        permitted_projects = self.request.user.get_permitted_projects(
            permission_key=VIEW_PROJECT
        )
        project = get_object_or_404(permitted_projects, pk=self.kwargs["project_pk"])

        queryset = project.segments.all()

        if self.action == "list":
            # TODO: at the moment, the UI only shows the name and description of the segment in the list view.
            #  we shouldn't return all of the rules and conditions in the list view.
            queryset = queryset.prefetch_related(
                "rules",
                "rules__conditions",
                "rules__rules",
                "rules__rules__conditions",
                "rules__rules__rules",
            )

        query_serializer = SegmentListQuerySerializer(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)

        identity_pk = query_serializer.validated_data.get("identity")
        if identity_pk:
            if identity_pk.isdigit():
                identity = Identity.objects.get(pk=identity_pk)
                segment_ids = [segment.id for segment in identity.get_segments()]
            else:
                segment_ids = EdgeIdentity.dynamo_wrapper.get_segment_ids(identity_pk)
            queryset = queryset.filter(id__in=segment_ids)

        search_term = query_serializer.validated_data.get("q")
        if search_term:
            queryset = queryset.filter(name__icontains=search_term)

        include_feature_specific = query_serializer.validated_data[
            "include_feature_specific"
        ]
        if include_feature_specific is False:
            queryset = queryset.filter(feature__isnull=True)

        return queryset

    @action(
        detail=True,
        methods=["GET"],
        url_path="associated-features",
        serializer_class=SegmentAssociatedFeatureStateSerializer,
    )
    def associated_features(self, request, *args, **kwargs):
        segment = self.get_object()
        queryset = FeatureState.objects.filter(feature_segment__segment=segment)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@swagger_auto_schema(responses={200: SegmentSerializer()}, method="get")
@api_view(["GET"])
def get_segment_by_uuid(request, uuid):
    accessible_projects = request.user.get_permitted_projects(VIEW_PROJECT)
    qs = Segment.objects.filter(project__in=accessible_projects)
    segment = get_object_or_404(qs, uuid=uuid)
    serializer = SegmentSerializer(instance=segment)
    return Response(serializer.data)
