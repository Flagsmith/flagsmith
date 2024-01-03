from django.db.models import QuerySet
from django.http import Http404
from rest_framework import viewsets

from environments.authentication import EnvironmentKeyAuthentication
from environments.permissions.permissions import EnvironmentKeyPermissions

from .models import SplitTest
from .permissions import SplitTestPermissions
from .serializers import ConversionEventSerializer, SplitTestSerializer


class ConversionEventViewSet(viewsets.ModelViewSet):
    permission_classes = (EnvironmentKeyPermissions,)
    authentication_classes = (EnvironmentKeyAuthentication,)
    serializer_class = ConversionEventSerializer
    http_method_names = ["post"]


class SplitTestViewSet(viewsets.ModelViewSet):
    permission_classes = (SplitTestPermissions,)
    serializer_class = SplitTestSerializer
    http_method_names = ["get"]

    def get_queryset(self) -> QuerySet[SplitTest]:
        environment_id = self.request.query_params.get("environment_id")
        if not environment_id:
            raise Http404(
                "Unable to find split test without environment_id query param set"
            )

        qs = SplitTest.objects.filter(environment_id=environment_id).select_related(
            "feature", "multivariate_feature_option"
        )

        # In order to keep split test results in the same order
        # between refreshes, order first by the feature name then
        # by the multivariate feature option id.
        return qs.order_by("feature__name", "multivariate_feature_option")
