from integrations.common.views import IntegrationCommonViewSet
from integrations.webhook.models import WebhookConfiguration
from integrations.webhook.serializers import WebhookConfigurationSerializer


class WebhookConfigurationViewSet(IntegrationCommonViewSet):
    serializer_class = WebhookConfigurationSerializer
    model_class = WebhookConfiguration
