from rest_framework import viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from features.models import Feature
from projects.permissions import IsProjectAdmin, NestedProjectPermissions

from .serializers import MultivariateFeatureOptionSerializer


class MultivariateFeatureOptionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsProjectAdmin]
    serializer_class = MultivariateFeatureOptionSerializer

    def get_permissions(self):
        return [
            IsAuthenticated(),
            NestedProjectPermissions(
                action_permission_map={
                    "list": "VIEW_PROJECT",
                    "detail": "VIEW_PROJECT",
                    "create": "CREATE_FEATURE",
                    "update": "CREATE_FEATURE",
                    "partial_update": "CREATE_FEATURE",
                    "destroy": "CREATE_FEATURE",
                }
            ),
        ]

    def get_queryset(self):
        feature = get_object_or_404(Feature, pk=self.kwargs["feature_pk"])
        return feature.multivariate_options.all()
