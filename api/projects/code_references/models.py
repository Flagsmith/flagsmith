from django.db import models


class FeatureFlagCodeReferencesScan(models.Model):
    """
    A JSON package of feature flag code references within a repository
    """

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="code_references",
    )

    repository_url = models.URLField()  # Provider-agnostic
    revision = models.CharField(max_length=100)
    code_references = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
