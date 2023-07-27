from integrations.common.views import ProjectIntegrationBaseViewSet
from integrations.datadog.models import DataDogConfiguration
from integrations.datadog.serializers import DataDogConfigurationSerializer


class DataDogConfigurationViewSet(ProjectIntegrationBaseViewSet):
    serializer_class = DataDogConfigurationSerializer
    model_class = DataDogConfiguration
