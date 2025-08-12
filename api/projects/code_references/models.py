from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.db.models.expressions import Func
from django.utils import timezone


class VCSFeatureFlagCodeReferences(models.Model):
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

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            GinIndex(  # Helps filtering code references by feature name
                Func(
                    models.F("code_references"),
                    models.Value("$[*].name"),
                    function="jsonb_path_query_array",
                ),
                name="code_references_feature_name",
            ),
        ]
