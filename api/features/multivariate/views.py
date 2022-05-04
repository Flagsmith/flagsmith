from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from projects.permissions import IsProjectAdmin

from .serializers import MultivariateFeatureOptionSerializer


class MultivariateFeatureOptionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsProjectAdmin]
    serializer_class = MultivariateFeatureOptionSerializer
