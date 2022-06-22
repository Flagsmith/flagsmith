from django.db import models

from integrations.slack.managers import SlackConfigurationManager
from projects.models import Project


class SlackConfiguration(models.Model):
    api_token = models.CharField(max_length=100, blank=False, null=False)
    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="slack_config"
    )
    created_date = models.DateTimeField(auto_now_add=True)

    objects = SlackConfigurationManager()

    # TODO
    def natural_key(self):
        return self.project_id, self.created_date, self.api_token


class SlackEnvironment(models.Model):
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

    class Meta:
        unique_together = ("slack_configuration", "environment")

    # TODO
    def natural_key(self):
        return self.slack_configuration_id, self.environment_id
