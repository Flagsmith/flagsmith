from typing import Any

from django.db import models

from core.models import SoftDeleteExportableModel


class AzureDevOpsConfiguration(SoftDeleteExportableModel):
    project = models.OneToOneField(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="azure_devops_config",
    )
    organisation_url = models.URLField(max_length=300)
    personal_access_token = models.CharField(max_length=300)
    labeling_enabled = models.BooleanField(default=False)
    tagging_enabled = models.BooleanField(default=False)

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.organisation_url = self.organisation_url.rstrip("/")
        super().save(*args, **kwargs)


class AzureDevOpsServiceHook(SoftDeleteExportableModel):
    configuration = models.ForeignKey(
        AzureDevOpsConfiguration,
        on_delete=models.CASCADE,
        related_name="service_hooks",
    )
    ado_project_id = models.UUIDField()
    ado_project_name = models.CharField(max_length=200)
    event_type = models.CharField(max_length=64)
    subscription_id = models.UUIDField()
    secret = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["configuration", "ado_project_id", "event_type"],
                name="unique_azure_devops_service_hook_per_event",
                condition=models.Q(deleted_at__isnull=True),
            ),
        ]
