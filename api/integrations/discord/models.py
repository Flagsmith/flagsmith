from django.db import models

from integrations.common.models import IntegrationsModel
from projects.models import Project


class DiscordConfiguration(IntegrationsModel):
    """Posts a project's audit log events to a Discord channel.

    `base_url` holds the channel's Discord webhook URL (Server Settings > Integrations >
    Webhooks). No API key is needed: the webhook URL carries its own token.
    """

    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="discord_config"
    )
    api_key = models.CharField(max_length=100, blank=True, default="")
