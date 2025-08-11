from common.environments.permissions import (
    UPDATE_FEATURE_STATE,
)
from common.projects.permissions import (
    CREATE_FEATURE,
    VIEW_PROJECT,
)
from drf_yasg.utils import swagger_auto_schema  # type: ignore[import-untyped]
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from environments.models import Environment
from features.models import Feature

from .models import MultivariateFeatureOption
from .serializers import MultivariateFeatureOptionSerializer


class MultivariateFeatureOptionPermissions(IsAuthenticated):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not super().has_permission(request, view):
            return False
        action = getattr(view, "action", None)
        if action in ["update", "partial_update"]:
            environment_id = request.data.get("environment_id")
            if not environment_id:
                return False

            try:
                environment = Environment.objects.get(id=environment_id)
                return request.user.has_environment_permission(  # type: ignore[union-attr]
                    UPDATE_FEATURE_STATE, environment
                )
            except Environment.DoesNotExist:
                return False

        return True

    def has_object_permission(
        self, request: Request, view: APIView, obj: MultivariateFeatureOption
    ) -> bool:
        action_permission_map = {
            "list": VIEW_PROJECT,
            "retrieve": VIEW_PROJECT,
            "create": CREATE_FEATURE,
            "destroy": CREATE_FEATURE,
        }

        action: str | None = getattr(view, "action", None)
        if action in ["update", "partial_update"]:
            return True

        permission = action_permission_map.get(action) if action else None
        if permission:
            return request.user.has_project_permission(permission, obj.feature.project)  # type: ignore[union-attr]

        return False


class MultivariateFeatureOptionViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    serializer_class = MultivariateFeatureOptionSerializer
    permission_classes = [MultivariateFeatureOptionPermissions]

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


@swagger_auto_schema(
    responses={200: MultivariateFeatureOptionSerializer()}, method="get"
)
@api_view(["GET"])
def get_mv_feature_option_by_uuid(request, uuid):  # type: ignore[no-untyped-def]
    accessible_projects = request.user.get_permitted_projects(VIEW_PROJECT)
    qs = MultivariateFeatureOption.objects.filter(
        feature__project__in=accessible_projects
    )
    mv_option = get_object_or_404(qs, uuid=uuid)
    serializer = MultivariateFeatureOptionSerializer(instance=mv_option)
    return Response(serializer.data)
