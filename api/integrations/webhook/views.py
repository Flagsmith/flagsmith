from integrations.common.views import EnvironmentIntegrationCommonViewSet
from integrations.webhook.models import WebhookConfiguration
from integrations.webhook.serializers import WebhookConfigurationSerializer


class WebhookConfigurationViewSet(EnvironmentIntegrationCommonViewSet):
    serializer_class = WebhookConfigurationSerializer
    model_class = WebhookConfiguration
