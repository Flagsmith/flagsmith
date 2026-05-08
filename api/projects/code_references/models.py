from django.db import models

from projects.code_references.types import JSONCodeReference, VCSProvider


class VCSRepository(models.Model):
    """
    A VCS repository that is scanned for feature flag code references
    """

    created_at = models.DateTimeField(auto_now_add=True)

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="vcs_repositories",
    )

    # Provider-agnostic URL to the web UI of the repository, e.g. https://github.flagsmith.com/backend/
    url = models.URLField()

    vcs_provider = models.CharField(
        max_length=50,
        choices=VCSProvider.choices,
    )

    last_scanned_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "url"],
                name="unique_vcs_repository",
            ),
        ]


class ScannedCodeReferences(models.Model):
    """
    A list of code references for a feature scanned from a VCS repository
    """

    created_at = models.DateTimeField(auto_now_add=True)

    feature = models.ForeignKey(
        "features.Feature",
        on_delete=models.CASCADE,
        related_name="scanned_code_references",
    )

    repository = models.ForeignKey(
        VCSRepository,
        on_delete=models.CASCADE,
        related_name="scanned_code_references",
    )

    revision = models.CharField(max_length=100)

    code_references = models.JSONField[list[JSONCodeReference]](default=list)

    code_references_hash = models.CharField(max_length=32)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["feature", "repository", "code_references_hash"],
                name="unique_scanned_code_references",
            ),
        ]
