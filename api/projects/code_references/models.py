from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.db.models.expressions import Func

from projects.code_references.types import JSONCodeReference, VCSProvider

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
        indexes = [
            GinIndex(  # Helps filtering code references by feature name
                Func(
                    models.F("code_references"),
                    models.Value("$[*].feature_name"),
                    function="jsonb_path_query_array",
                ),
                name="code_references_feature_name",
            ),
        ]
