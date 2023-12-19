from rest_framework import generics

from external_resource.models import ExternalResource, FeatureExternalResource
from external_resource.serializers import (
    ExternalResourceSerializer,
    FeatureExternalResourceSerializer,
)


class ExternalResourceListCreateView(generics.ListCreateAPIView):
    queryset = ExternalResource.objects.all()
    serializer_class = ExternalResourceSerializer


class ExternalResourceRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ExternalResource.objects.all()
    serializer_class = ExternalResourceSerializer


class FeatureExternalResourceListCreateView(generics.ListCreateAPIView):
    queryset = FeatureExternalResource.objects.all()
    serializer_class = FeatureExternalResourceSerializer


class FeatureExternalResourceRetrieveUpdateDestroyView(
    generics.RetrieveUpdateDestroyAPIView
):
    queryset = FeatureExternalResource.objects.all()
    serializer_class = FeatureExternalResourceSerializer


class ExternalResourceSearchView(generics.ListAPIView):
    serializer_class = ExternalResourceSerializer

    def get_queryset(self):
        search_query = self.request.query_params.get("search", "")
        return ExternalResource.objects.filter(url__icontains=search_query)
