from django.db import models

from core.models import SoftDeleteExportableModel


class GitLabConfiguration(SoftDeleteExportableModel):
    project = models.OneToOneField(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="gitlab_config",
    )
    gitlab_instance_url = models.URLField(max_length=200)
    access_token = models.CharField(max_length=300)


class GitLabWebhook(SoftDeleteExportableModel):
    gitlab_configuration = models.ForeignKey(
        GitLabConfiguration,
        on_delete=models.CASCADE,
        related_name="webhooks",
    )
    gitlab_hook_id = models.PositiveIntegerField()
    gitlab_path_with_namespace = models.TextField()
    gitlab_project_id = models.PositiveIntegerField()
    secret = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["gitlab_configuration", "gitlab_path_with_namespace"],
                name="unique_gitlab_webhook_per_config_path",
                condition=models.Q(deleted_at__isnull=True),
            ),
        ]
