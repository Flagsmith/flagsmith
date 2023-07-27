from integrations.common.views import ProjectIntegrationBaseViewSet
from integrations.new_relic.models import NewRelicConfiguration
from integrations.new_relic.serializers import NewRelicConfigurationSerializer


class NewRelicConfigurationViewSet(ProjectIntegrationBaseViewSet):
    serializer_class = NewRelicConfigurationSerializer
    model_class = NewRelicConfiguration
