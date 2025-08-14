from django.db import models


class FeatureFlagCodeReferencesScan(models.Model):
    """
    A scan of feature flag code references in a repository
    """

    class Providers(models.TextChoices):
        GITHUB = "github", "GitHub"

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="code_references",
    )

    # Provider-agnostic URL to the web UI of the repository, e.g. https://github.flagsmith.com/backend/
    repository_url = models.URLField()

    vcs_provider = models.CharField(
        max_length=50,
        choices=Providers.choices,
        default=Providers.GITHUB,  # TODO: Remove when adding other providers
    )
    revision = models.CharField(max_length=100)
    code_references = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
