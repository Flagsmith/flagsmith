from integrations.amplitude.models import AmplitudeConfiguration
from integrations.amplitude.serializers import AmplitudeConfigurationSerializer
from integrations.common.views import EnvironmentIntegrationCommonViewSet


class AmplitudeConfigurationViewSet(EnvironmentIntegrationCommonViewSet):
    serializer_class = AmplitudeConfigurationSerializer  # type: ignore[assignment]
    pagination_class = None  # set here to ensure documentation is correct
    model_class = AmplitudeConfiguration  # type: ignore[assignment]
