from integrations.common.views import IntegrationCommonViewSet
from integrations.mixpanel.models import MixpanelConfiguration
from integrations.mixpanel.serializers import MixpanelConfigurationSerializer


class MixpanelConfigurationViewSet(IntegrationCommonViewSet):
    serializer_class = MixpanelConfigurationSerializer
    model_class = MixpanelConfiguration
