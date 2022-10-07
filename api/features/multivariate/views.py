from rest_framework import viewsets
from rest_framework.generics import get_object_or_404

from features.models import Feature
from projects.permissions import (
    NestedProjectMasterAPIKeyPermissions,
    NestedProjectPermissions,
)

from .serializers import MultivariateFeatureOptionSerializer


class MultivariateFeatureOptionViewSet(viewsets.ModelViewSet):
    permission_classes = [
        NestedProjectPermissions | NestedProjectMasterAPIKeyPermissions
    ]
    serializer_class = MultivariateFeatureOptionSerializer

    def get_permissions(self):
        action_permission_map = {
            "list": "VIEW_PROJECT",
            "detail": "VIEW_PROJECT",
            "create": "CREATE_FEATURE",
            "update": "CREATE_FEATURE",
            "partial_update": "CREATE_FEATURE",
            "destroy": "CREATE_FEATURE",
        }

        permission_kwargs = {
            "action_permission_map": action_permission_map,
            "get_project_from_object_callable": lambda o: o.feature.project,
        }
        return [
            permission(**permission_kwargs) for permission in self.permission_classes
        ]

    def get_queryset(self):
        feature = get_object_or_404(Feature, pk=self.kwargs["feature_pk"])
        return feature.multivariate_options.all()
