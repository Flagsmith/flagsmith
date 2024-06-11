from integrations.common.views import EnvironmentIntegrationCommonViewSet
from integrations.grafana.models import GrafanaConfiguration
from integrations.grafana.serializers import GrafanaConfigurationSerializer


class GrafanaConfigurationViewSet(EnvironmentIntegrationCommonViewSet):
    serializer_class = GrafanaConfigurationSerializer
    pagination_class = None  # set here to ensure documentation is correct
    model_class = GrafanaConfiguration
