from integrations.common.views import ProjectIntegrationBaseViewSet
from integrations.discord.models import DiscordConfiguration
from integrations.discord.serializers import DiscordConfigurationSerializer


class DiscordConfigurationViewSet(ProjectIntegrationBaseViewSet):
    serializer_class = DiscordConfigurationSerializer  # type: ignore[assignment]
    model_class = DiscordConfiguration  # type: ignore[assignment]
