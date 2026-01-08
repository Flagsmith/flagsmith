from common.projects.permissions import (
    CREATE_FEATURE,
    VIEW_PROJECT,
)
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from features.models import Feature
from projects.permissions import NestedProjectPermissions

from .models import MultivariateFeatureOption
from .serializers import MultivariateFeatureOptionSerializer


@method_decorator(
    name="list",
    decorator=extend_schema(
        tags=["mcp"],
        extensions={
            "x-mcp-name": "list_feature_multivariate_options",
            "x-mcp-description": "Retrieves all multivariate options for a feature flag.",
        },
    ),
)
@method_decorator(
    name="create",
    decorator=extend_schema(
        tags=["mcp"],
        extensions={
            "x-mcp-name": "create_feature_multivariate_option",
            "x-mcp-description": "Creates a new multivariate option for a feature flag.",
        },
    ),
)
@method_decorator(
    name="update",
    decorator=extend_schema(
        tags=["mcp"],
        extensions={
            "x-mcp-name": "update_feature_multivariate_option",
            "x-mcp-description": "Updates an existing multivariate option.",
        },
    ),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(
        tags=["mcp"],
        extensions={
            "x-mcp-name": "delete_feature_multivariate_option",
            "x-mcp-description": "Deletes a multivariate option.",
        },
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

    def get_queryset(self):  # type: ignore[no-untyped-def]
        if getattr(self, "swagger_fake_view", False):
            return MultivariateFeatureOption.objects.none()

        feature = get_object_or_404(Feature, pk=self.kwargs["feature_pk"])
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
