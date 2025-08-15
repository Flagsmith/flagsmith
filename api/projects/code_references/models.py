from django.db import models

from projects.code_references.types import JSONCodeReference, VCSProvider


class FeatureFlagCodeReferencesScan(models.Model):
    """
    A scan of feature flag code references in a repository
    """

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="code_references",
    )

    # Provider-agnostic URL to the web UI of the repository, e.g. https://github.flagsmith.com/backend/
    repository_url = models.URLField()

    vcs_provider = models.CharField(
        max_length=50,
        choices=VCSProvider.choices,
        default=VCSProvider.GITHUB,  # TODO: Remove when adding other providers
    )
    revision = models.CharField(max_length=100)
    code_references = models.JSONField[list[JSONCodeReference]](default=list)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
