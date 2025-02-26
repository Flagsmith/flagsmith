from integrations.common.views import EnvironmentIntegrationCommonViewSet
from integrations.segment.models import SegmentConfiguration
from integrations.segment.serializers import SegmentConfigurationSerializer


class SegmentConfigurationViewSet(EnvironmentIntegrationCommonViewSet):
    serializer_class = SegmentConfigurationSerializer  # type: ignore[assignment]
    pagination_class = None  # set here to ensure documentation is correct
    model_class = SegmentConfiguration  # type: ignore[assignment]
