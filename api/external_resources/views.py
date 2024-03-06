from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import ExternalResources
from .serializers import ExternalResourcesSerializer


class ExternalResourcesViewSet(viewsets.ModelViewSet):
    serializer_class = ExternalResourcesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if "pk" in self.kwargs:
            return ExternalResources.objects.filter(id=self.kwargs["pk"])
        else:
            return ExternalResources.objects.all()

    def perform_update(self, serializer):
        external_resource_id = int(self.kwargs["id"])
        serializer.save(id=external_resource_id)


class ExternalResourcesByFeatureViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ExternalResourcesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        features_pk = self.kwargs["features_pk"]
        return ExternalResources.objects.filter(feature=features_pk)
