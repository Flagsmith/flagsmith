from integrations.amplitude.models import AmplitudeConfiguration
from integrations.amplitude.serializers import AmplitudeConfigurationSerializer
from integrations.common.views import IntegrationCommonViewSet


class AmplitudeConfigurationViewSet(IntegrationCommonViewSet):
    serializer_class = AmplitudeConfigurationSerializer
    pagination_class = None  # set here to ensure documentation is correct
    model_class = AmplitudeConfiguration
