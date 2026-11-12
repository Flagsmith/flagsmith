from common.projects.permissions import (
    CREATE_FEATURE,
    VIEW_PROJECT,
)
from django.db import transaction
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from experimentation.feature_state_metadata import check_no_live_experiment
from features.models import Feature
from projects.permissions import NestedProjectPermissions

from .models import MultivariateFeatureOption
from .serializers import MultivariateFeatureOptionSerializer

# What makes a variation. `default_percentage_allocation` is left out: the
# dashboard always sends it as 0, and it only seeds new environments.
VARIATION_FIELDS = (
    "type",
    "string_value",
    "integer_value",
    "boolean_value",
    "key",
    "feature",
)


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
        url_feature = get_object_or_404(
            Feature.objects.filter(project__id=project_pk), pk=feature_pk
        )
        if "feature" in request.data and str(request.data.get("feature")) != str(
            url_feature.id
        ):
            raise ValidationError({"feature": "Feature must match the URL."})
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):  # type: ignore[no-untyped-def]
        url_feature = get_object_or_404(
            Feature.objects.filter(project__id=self.kwargs["project_pk"]),
            pk=self.kwargs["feature_pk"],
        )
        if serializer.validated_data["feature"] != url_feature:
            raise ValidationError({"feature": "Feature must match the URL."})
        with transaction.atomic():
            Feature.objects.select_for_update().filter(pk=url_feature.pk).exists()
            check_no_live_experiment(url_feature.id)
            super().perform_create(serializer)

    def perform_update(self, serializer):  # type: ignore[no-untyped-def]
        instance = serializer.instance
        data = serializer.validated_data
        # The dashboard PUTs every option on each save, changed or not, so only
        # a change to the variation itself is checked against experiments.
        if not any(
            field in data and data[field] != getattr(instance, field)
            for field in VARIATION_FIELDS
        ):
            super().perform_update(serializer)
            return

        features = {instance.feature, data.get("feature", instance.feature)}
        with transaction.atomic():
            list(
                Feature.objects.select_for_update()
                .filter(pk__in=[feature.pk for feature in features])
                .order_by("pk")
                .values_list("pk", flat=True)
            )
            for feature in features:
                check_no_live_experiment(feature.id)
            super().perform_update(serializer)

    def perform_destroy(self, instance):  # type: ignore[no-untyped-def]
        with transaction.atomic():
            Feature.objects.select_for_update().filter(pk=instance.feature_id).exists()
            check_no_live_experiment(instance.feature_id)
            super().perform_destroy(instance)

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
