from django.utils.decorators import method_decorator
from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import viewsets

from .models import MetadataField
from .permissions import MetadataFieldPermissions
from .serializers import MetadataFieldSerializer


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
        organisation_id = self.request.query_params.get("organisation")
        if organisation_id:
            queryset = queryset.filter(organisation__id=organisation_id)

        return queryset
