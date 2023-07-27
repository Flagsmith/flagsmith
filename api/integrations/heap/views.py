from integrations.common.views import EnvironmentIntegrationCommonViewSet
from integrations.heap.models import HeapConfiguration
from integrations.heap.serializers import HeapConfigurationSerializer


class HeapConfigurationViewSet(EnvironmentIntegrationCommonViewSet):
    serializer_class = HeapConfigurationSerializer
    model_class = HeapConfiguration
