from integrations.common.views import IntegrationCommonViewSet
from integrations.segment.models import SegmentConfiguration
from integrations.segment.serializers import SegmentConfigurationSerializer


class SegmentConfigurationViewSet(IntegrationCommonViewSet):
    serializer_class = SegmentConfigurationSerializer
    pagination_class = None  # set here to ensure documentation is correct
    model_class = SegmentConfiguration
