from integrations.common.views import EnvironmentIntegrationCommonViewSet
from integrations.rudderstack.models import RudderstackConfiguration
from integrations.rudderstack.serializers import (
    RudderstackConfigurationSerializer,
)


class RudderstackConfigurationViewSet(EnvironmentIntegrationCommonViewSet):
    serializer_class = RudderstackConfigurationSerializer  # type: ignore[assignment]
    pagination_class = None  # set here to ensure documentation is correct
    model_class = RudderstackConfiguration  # type: ignore[assignment]
