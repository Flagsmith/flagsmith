import logging
from contextlib import suppress

from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from flag_engine.environments.builders import build_environment_model
from flag_engine.identities.builders import build_identity_model
from flag_engine.segments.evaluator import get_identity_segments
from rest_framework import viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from environments.dynamodb import DynamoEnvironmentWrapper
from environments.identities.models import Identity

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
            )
        ]
    ),
)
class SegmentViewSet(viewsets.ModelViewSet):
    serializer_class = SegmentSerializer
    permission_classes = [IsAuthenticated, SegmentPermissions]

    def get_queryset(self):
        project = get_object_or_404(
            self.request.user.get_permitted_projects(["VIEW_PROJECT"]),
            pk=self.kwargs["project_pk"],
        )
        queryset = project.segments.all()

        identity_pk = self.request.query_params.get("identity")
        if identity_pk:
            if identity_pk.isdigit():
                identity = Identity.objects.get(pk=identity_pk)
                segment_ids = [segment.id for segment in identity.get_segments()]
            else:
                segment_ids = _get_segment_ids_for_edge_identity(identity_pk)
            queryset = queryset.filter(id__in=segment_ids)

        return queryset


def _get_segment_ids_for_edge_identity(identity_pk: str) -> list:
    with suppress(ObjectDoesNotExist):
        identity_document = Identity.dynamo_wrapper.get_item_from_uuid(identity_pk)
        identity = build_identity_model(identity_document)
        environment_wrapper = DynamoEnvironmentWrapper()
        environment = build_environment_model(
            environment_wrapper.get_item(identity.environment_api_key)
        )
        segments = get_identity_segments(environment, identity)
        return [segment.id for segment in segments]
    return []
