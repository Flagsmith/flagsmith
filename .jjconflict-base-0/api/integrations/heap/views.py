from integrations.common.views import EnvironmentIntegrationCommonViewSet
from integrations.heap.models import HeapConfiguration
from integrations.heap.serializers import HeapConfigurationSerializer


class HeapConfigurationViewSet(EnvironmentIntegrationCommonViewSet):
    serializer_class = HeapConfigurationSerializer  # type: ignore[assignment]
    model_class = HeapConfiguration  # type: ignore[assignment]
