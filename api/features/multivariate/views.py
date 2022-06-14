from rest_framework import viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from features.models import Feature
from projects.permissions import IsProjectAdmin

from .serializers import MultivariateFeatureOptionSerializer


class MultivariateFeatureOptionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsProjectAdmin]
    serializer_class = MultivariateFeatureOptionSerializer

    def get_queryset(self):
        feature = get_object_or_404(Feature, pk=self.kwargs["feature_pk"])
        return feature.multivariate_options.all()
