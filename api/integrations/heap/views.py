from integrations.common.views import IntegrationCommonViewSet
from integrations.heap.models import HeapConfiguration
from integrations.heap.serializers import HeapConfigurationSerializer


class HeapConfigurationViewSet(IntegrationCommonViewSet):
    serializer_class = HeapConfigurationSerializer
    model_class = HeapConfiguration
