from integrations.common.views import EnvironmentIntegrationCommonViewSet
from integrations.mixpanel.models import MixpanelConfiguration
from integrations.mixpanel.serializers import MixpanelConfigurationSerializer


class MixpanelConfigurationViewSet(EnvironmentIntegrationCommonViewSet):
    serializer_class = MixpanelConfigurationSerializer  # type: ignore[assignment]
    model_class = MixpanelConfiguration  # type: ignore[assignment]
