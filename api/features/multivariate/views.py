from common.projects.permissions import (
    CREATE_FEATURE,
    VIEW_PROJECT,
)
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from experimentation.feature_state_metadata import has_live_experiment
from features.constants import LIVE_EXPERIMENT_MV_OPTIONS_MESSAGE
from features.models import Feature
from projects.permissions import NestedProjectPermissions

from .models import MultivariateFeatureOption
from .serializers import MultivariateFeatureOptionSerializer


@method_decorator(
    name="list",
    decorator=extend_schema(
        tags=["mcp"],
        operation_id="list_feature_multivariate_options",
        description="Retrieves all multivariate options for a feature flag.",
    ),
)
@method_decorator(
    name="create",
    decorator=extend_schema(
        tags=["mcp"],
        operation_id="create_feature_multivariate_option",
        description="Creates a new multivariate option for a feature flag.",
    ),
)
@method_decorator(
    name="update",
    decorator=extend_schema(
        tags=["mcp"],
        operation_id="update_feature_multivariate_option",
        description="Updates an existing multivariate option.",
    ),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(
        tags=["mcp"],
        operation_id="delete_feature_multivariate_option",
        description="Deletes a multivariate option.",
    ),
)
class MultivariateFeatureOptionViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    serializer_class = MultivariateFeatureOptionSerializer

    def get_permissions(self):  # type: ignore[no-untyped-def]
        return [
            NestedProjectPermissions(
                action_permission_map={
                    "list": VIEW_PROJECT,
                    "detail": VIEW_PROJECT,
                    "create": CREATE_FEATURE,
                    "update": CREATE_FEATURE,
                    "partial_update": CREATE_FEATURE,
                    "destroy": CREATE_FEATURE,
                },
                get_project_from_object_callable=lambda o: o.feature.project,  # type: ignore[attr-defined]
            )
        ]

    def create(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        feature_pk = self.kwargs.get("feature_pk")
        project_pk = self.kwargs.get("project_pk")
        get_object_or_404(Feature.objects.filter(project__id=project_pk), pk=feature_pk)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):  # type: ignore[no-untyped-def]
        url_feature = get_object_or_404(
            Feature.objects.filter(project__id=self.kwargs["project_pk"]),
            pk=self.kwargs["feature_pk"],
        )
        if serializer.validated_data["feature"] != url_feature:
            raise ValidationError({"feature": "Feature must match the URL."})
        self._check_no_live_experiment(url_feature)
        super().perform_create(serializer)

    def perform_update(self, serializer):  # type: ignore[no-untyped-def]
        self._check_no_live_experiment(serializer.instance.feature)
        if "feature" in serializer.validated_data:
            self._check_no_live_experiment(serializer.validated_data["feature"])
        super().perform_update(serializer)

    def perform_destroy(self, instance):  # type: ignore[no-untyped-def]
        self._check_no_live_experiment(instance.feature)
        super().perform_destroy(instance)

    def _check_no_live_experiment(self, feature: Feature) -> None:
        if has_live_experiment(feature.id):
            raise ValidationError(LIVE_EXPERIMENT_MV_OPTIONS_MESSAGE)

    def get_queryset(self):  # type: ignore[no-untyped-def]
        if getattr(self, "swagger_fake_view", False):
            return MultivariateFeatureOption.objects.none()

        feature = get_object_or_404(
            Feature.objects.filter(project__id=self.kwargs["project_pk"]),
            pk=self.kwargs["feature_pk"],
        )
        return feature.multivariate_options.all()


@extend_schema(responses={200: MultivariateFeatureOptionSerializer()})
@api_view(["GET"])
def get_mv_feature_option_by_uuid(request, uuid):  # type: ignore[no-untyped-def]
    accessible_projects = request.user.get_permitted_projects(VIEW_PROJECT)
    qs = MultivariateFeatureOption.objects.filter(
        feature__project__in=accessible_projects
    )
    mv_option = get_object_or_404(qs, uuid=uuid)
    serializer = MultivariateFeatureOptionSerializer(instance=mv_option)
    return Response(serializer.data)
