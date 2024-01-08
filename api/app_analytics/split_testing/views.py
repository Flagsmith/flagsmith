from django.db.models import QuerySet
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets

from environments.authentication import EnvironmentKeyAuthentication
from environments.permissions.permissions import EnvironmentKeyPermissions

from .models import SplitTest
from .permissions import SplitTestPermissions
from .serializers import (
    ConversionEventSerializer,
    SplitTestQuerySerializer,
    SplitTestSerializer,
)


class ConversionEventViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    permission_classes = (EnvironmentKeyPermissions,)
    authentication_classes = (EnvironmentKeyAuthentication,)
    serializer_class = ConversionEventSerializer


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(query_serializer=SplitTestQuerySerializer()),
)
class SplitTestViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (SplitTestPermissions,)
    serializer_class = SplitTestSerializer

    def get_queryset(self) -> QuerySet[SplitTest]:
        query_serializer = SplitTestQuerySerializer(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)
        qs = SplitTest.objects.filter(
            environment_id=query_serializer.validated_data["environment_id"]
        ).select_related("feature", "multivariate_feature_option")

        # In order to keep split test results in the same order
        # between refreshes, order first by the feature name then
        # by the multivariate feature option id.
        return qs.order_by("feature__name", "multivariate_feature_option")
