import logging

from core.permissions import HasMasterAPIKey
from django.utils.decorators import method_decorator
from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from app.pagination import CustomPagination
from environments.identities.models import Identity
from features.models import FeatureState
from features.serializers import SegmentAssociatedFeatureStateSerializer

from .models import Segment
from .permissions import SegmentPermissions
from .serializers import SegmentSerializer

logger = logging.getLogger()


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "identity",
                openapi.IN_QUERY,
                "Optionally provide the id of an identity to get only the segments they match",
                required=False,
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "q",
                openapi.IN_QUERY,
                "Search term to find segment with given term in their name",
                required=False,
                type=openapi.TYPE_STRING,
            ),
        ]
    ),
)
class SegmentViewSet(viewsets.ModelViewSet):
    serializer_class = SegmentSerializer
    permission_classes = [IsAuthenticated, SegmentPermissions]
    pagination_class = CustomPagination

    def get_queryset(self):
        project = get_object_or_404(
            self.request.user.get_permitted_projects(["VIEW_PROJECT"]),
            pk=self.kwargs["project_pk"],
        )

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

        identity_pk = self.request.query_params.get("identity")
        if identity_pk:
            if identity_pk.isdigit():
                identity = Identity.objects.get(pk=identity_pk)
                segment_ids = [segment.id for segment in identity.get_segments()]
            else:
                segment_ids = Identity.dynamo_wrapper.get_segment_ids(identity_pk)
            queryset = queryset.filter(id__in=segment_ids)

        search_term = self.request.query_params.get("q")
        if search_term:
            queryset = queryset.filter(name__icontains=search_term)

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
@permission_classes([IsAuthenticated | HasMasterAPIKey])
def get_segment_by_uuid(request, uuid):
    if getattr(request, "master_api_key", None):
        accessible_projects = request.master_api_key.organisation.projects.all()
    else:
        accessible_projects = request.user.get_permitted_projects(["VIEW_PROJECT"])
    qs = Segment.objects.filter(project__in=accessible_projects)
    segment = get_object_or_404(qs, uuid=uuid)
    serializer = SegmentSerializer(instance=segment)
    return Response(serializer.data)
