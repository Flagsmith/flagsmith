from integrations.common.views import EnvironmentIntegrationCommonViewSet

from .models import SentryChangeTrackingConfiguration
from .serializers import SentryChangeTrackingConfigurationSerializer


class SentryChangeTrackingConfigurationViewSet(EnvironmentIntegrationCommonViewSet):
    model_class = SentryChangeTrackingConfiguration  # type: ignore[assignment]
    pagination_class = None  # set here to ensure documentation is correct
    serializer_class = SentryChangeTrackingConfigurationSerializer  # type: ignore[assignment]
