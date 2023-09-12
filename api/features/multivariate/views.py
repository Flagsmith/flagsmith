from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from features.models import Feature
from projects.permissions import (
    CREATE_FEATURE,
    VIEW_PROJECT,
    NestedProjectPermissions,
)

from .models import MultivariateFeatureOption
from .serializers import MultivariateFeatureOptionSerializer


class MultivariateFeatureOptionViewSet(viewsets.ModelViewSet):
    serializer_class = MultivariateFeatureOptionSerializer

    def get_permissions(self):
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
                get_project_from_object_callable=lambda o: o.feature.project,
            )
        ]

    def create(self, request, *args, **kwargs):
        feature_pk = self.kwargs.get("feature_pk")
        project_pk = self.kwargs.get("project_pk")
        get_object_or_404(Feature.objects.filter(project__id=project_pk), pk=feature_pk)
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return MultivariateFeatureOption.objects.none()

        feature = get_object_or_404(Feature, pk=self.kwargs["feature_pk"])
        return feature.multivariate_options.all()


@swagger_auto_schema(
    responses={200: MultivariateFeatureOptionSerializer()}, method="get"
)
@api_view(["GET"])
def get_mv_feature_option_by_uuid(request, uuid):
    accessible_projects = request.user.get_permitted_projects(VIEW_PROJECT)
    qs = MultivariateFeatureOption.objects.filter(
        feature__project__in=accessible_projects
    )
    mv_option = get_object_or_404(qs, uuid=uuid)
    serializer = MultivariateFeatureOptionSerializer(instance=mv_option)
    return Response(serializer.data)
