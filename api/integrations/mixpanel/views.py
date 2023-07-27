from integrations.common.views import EnvironmentIntegrationCommonViewSet
from integrations.mixpanel.models import MixpanelConfiguration
from integrations.mixpanel.serializers import MixpanelConfigurationSerializer


class MixpanelConfigurationViewSet(EnvironmentIntegrationCommonViewSet):
    serializer_class = MixpanelConfigurationSerializer
    model_class = MixpanelConfiguration
