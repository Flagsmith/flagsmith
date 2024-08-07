from integrations.common.views import ProjectIntegrationBaseViewSet
from integrations.grafana.models import GrafanaConfiguration
from integrations.grafana.serializers import GrafanaConfigurationSerializer


class GrafanaConfigurationViewSet(ProjectIntegrationBaseViewSet):
    serializer_class = GrafanaConfigurationSerializer
    pagination_class = None  # set here to ensure documentation is correct
    model_class = GrafanaConfiguration
