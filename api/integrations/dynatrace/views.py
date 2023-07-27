from integrations.common.views import EnvironmentIntegrationCommonViewSet
from integrations.dynatrace.models import DynatraceConfiguration
from integrations.dynatrace.serializers import DynatraceConfigurationSerializer


class DynatraceConfigurationViewSet(EnvironmentIntegrationCommonViewSet):
    serializer_class = DynatraceConfigurationSerializer
    pagination_class = None  # set here to ensure documentation is correct
    model_class = DynatraceConfiguration
