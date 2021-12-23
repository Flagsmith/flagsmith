from django.db import models
from django_lifecycle import BEFORE_SAVE, LifecycleModel, hook

from projects.models import Project

from .slack import SlackWrapper


class SlackConfiguration(models.Model):
    api_token = models.CharField(max_length=100, blank=False, null=False)
    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="slack_config"
    )
    created_date = models.DateTimeField(auto_now_add=True)


class SlackEnvironment(LifecycleModel):
    slack_configuration = models.ForeignKey(
        SlackConfiguration, related_name="env_config", on_delete=models.CASCADE
    )
    channel_id = models.CharField(
        max_length=50,
        help_text="Id of the slack channel to post messages to",
        blank=False,
        null=False,
    )
    environment = models.ForeignKey(
        "environments.Environment",
        related_name="slack_environment",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )
    enabled = models.BooleanField(default=True)

    @hook(BEFORE_SAVE)
    def join_channel(self):
        SlackWrapper(
            api_token=self.slack_configuration.api_token, channel_id=self.channel_id
        ).join_channel()

    class Meta:
        unique_together = ("slack_configuration", "environment")
