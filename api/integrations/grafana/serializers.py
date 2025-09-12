from integrations.common.serializers import (
    BaseOrganisationIntegrationModelSerializer,
    BaseProjectIntegrationModelSerializer,
)
from integrations.grafana.models import (
    GrafanaOrganisationConfiguration,
    GrafanaProjectConfiguration,
)


class GrafanaProjectConfigurationSerializer(
    BaseProjectIntegrationModelSerializer,
):
    class Meta:
        model = GrafanaProjectConfiguration
        fields = ("id", "base_url", "api_key")


class GrafanaOrganisationConfigurationSerializer(
    BaseOrganisationIntegrationModelSerializer,
):
    class Meta:
        model = GrafanaOrganisationConfiguration
        fields = ("id", "base_url", "api_key")
