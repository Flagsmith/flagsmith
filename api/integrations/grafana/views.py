from integrations.common.views import (
    OrganisationIntegrationBaseViewSet,
    ProjectIntegrationBaseViewSet,
)
from integrations.grafana.models import (
    GrafanaOrganisationConfiguration,
    GrafanaProjectConfiguration,
)
from integrations.grafana.serializers import (
    GrafanaOrganisationConfigurationSerializer,
    GrafanaProjectConfigurationSerializer,
)


class GrafanaProjectConfigurationViewSet(ProjectIntegrationBaseViewSet):
    serializer_class = GrafanaProjectConfigurationSerializer
    pagination_class = None  # set here to ensure documentation is correct
    model_class = GrafanaProjectConfiguration


class GrafanaOrganisationConfigurationViewSet(OrganisationIntegrationBaseViewSet):
    serializer_class = GrafanaOrganisationConfigurationSerializer
    pagination_class = None  # set here to ensure documentation is correct
    model_class = GrafanaOrganisationConfiguration
