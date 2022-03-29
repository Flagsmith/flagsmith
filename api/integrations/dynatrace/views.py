from integrations.common.views import IntegrationCommonViewSet
from integrations.dynatrace.models import DynatraceConfiguration
from integrations.dynatrace.serializers import DynatraceConfigurationSerializer


class DynatraceConfigurationViewSet(IntegrationCommonViewSet):
    serializer_class = DynatraceConfigurationSerializer
    pagination_class = None  # set here to ensure documentation is correct
    model_class = DynatraceConfiguration
