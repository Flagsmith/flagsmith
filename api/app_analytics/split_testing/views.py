from typing import Any

from django.db.models import F, QuerySet
from django.utils.decorators import method_decorator
from drf_yasg.utils import no_body, swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.response import Response

from environments.authentication import EnvironmentKeyAuthentication
from environments.permissions.permissions import EnvironmentKeyPermissions
from features.models import FeatureState

from .models import ConversionEventType, SplitTest
from .permissions import ConversionEventTypePermissions, SplitTestPermissions
from .serializers import (
    ConversionEventSerializer,
    ConversionEventTypeQuerySerializer,
    ConversionEventTypeSerializer,
    SplitTestQuerySerializer,
    SplitTestSerializer,
)


class CreateConversionEventView(CreateAPIView):
    permission_classes = (EnvironmentKeyPermissions,)
    authentication_classes = (EnvironmentKeyAuthentication,)
    serializer_class = ConversionEventSerializer

    @swagger_auto_schema(request_body=no_body, responses={202: ""})
    def post(self, *args: list[Any], **kwargs: dict[str, Any]) -> Response:
        response = super().post(*args, **kwargs)

        # Return an empty response to the client to keep options
        # open to process this in a task one day.
        if response.status_code == 201:
            return Response(status=status.HTTP_202_ACCEPTED)

        return response


class ConversionEventTypeView(ListAPIView):
    permission_classes = (ConversionEventTypePermissions,)
    serializer_class = ConversionEventTypeSerializer

    def get_queryset(self) -> QuerySet[ConversionEventType]:
        query_serializer = ConversionEventTypeQuerySerializer(
            data=self.request.query_params
        )
        query_serializer.is_valid(raise_exception=True)

        return ConversionEventType.objects.filter(
            environment_id=query_serializer.validated_data["environment_id"]
        ).order_by("name")


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
            conversion_event_type_id=query_serializer.validated_data[
                "conversion_event_type_id"
            ]
        ).select_related("feature", "multivariate_feature_option")

        # In order to keep split test results in the same order
        # between refreshes, order first by the feature name then
        # by the control (the null multivariate) and lastly by
        # the multivariate feature option id.
        return qs.order_by(
            "feature__name",
            F("multivariate_feature_option").asc(nulls_first=True),
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()

        feature_ids = set()
        environment_id = None
        for split_test in self.paginate_queryset(self.get_queryset()):
            feature_ids.add(split_test.feature_id)
            if environment_id:
                assert split_test.environment_id == environment_id
            else:
                environment_id = split_test.environment_id

        # The feature state value objects are needed for the
        # control group instead of a multivariate record.
        queryset = FeatureState.objects.select_related("feature_state_value").filter(
            environment_id=environment_id,
            identity__isnull=True,
            feature_segment__isnull=True,
            feature_id__in=feature_ids,
        )

        context["feature_states_by_env_feature_pair"] = {}
        for feature_state in queryset:
            context["feature_states_by_env_feature_pair"][
                (environment_id, feature_state.feature_id)
            ] = feature_state

        return context
