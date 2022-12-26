from django.utils.decorators import method_decorator
from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.decorators import action

from .models import MetadataField
from .permissions import MetadataFieldPermissions
from .serializers import MetadataFieldSerializer, MetadataSerializer

metadata_resource_map = {
    "feature": "features",
    "environment": "environments",
    "project": "projects",
}


class MetadataViewSet(viewsets.ModelViewSet):
    serializer_class = MetadataSerializer

    @action(
        detail=False,
        url_path=r"supported-objects",
        methods=["get"],
    )
    def get_supported_object_types(self):
        return metadata_resource_map.keys()

    def perform_create(self, serializer):
        serializer.save()


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "organisation",
                openapi.IN_QUERY,
                "ID of the organisation to filter by.",
                required=False,
                type=openapi.TYPE_INTEGER,
            )
        ]
    ),
)
class MetadataFieldViewSet(viewsets.ModelViewSet):
    permission_classes = [MetadataFieldPermissions]
    serializer_class = MetadataFieldSerializer

    def get_queryset(self):
        queryset = MetadataField.objects.filter(
            organisation__in=self.request.user.organisations.all()
        )
        queryset = self.request.user.get_permitted_projects(
            permissions=["VIEW_PROJECT"]
        )
        organisation_id = self.request.query_params.get("organisation")
        if organisation_id:
            queryset = queryset.filter(organisation__id=organisation_id)

        return queryset
