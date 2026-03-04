from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django_lifecycle import (  # type: ignore[import-untyped]
    BEFORE_SAVE,
    LifecycleModel,
    hook,
)

from projects.code_references.types import JSONCodeReference, VCSProvider


class FeatureFlagCodeReferencesScan(LifecycleModel):  # type: ignore[misc]
    """
    A scan of feature flag code references in a repository
    """

    project = models.ForeignKey(  # type: ignore[var-annotated]
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="code_references",
    )

    # Provider-agnostic URL to the web UI of the repository, e.g. https://github.flagsmith.com/backend/
    repository_url = models.URLField()  # type: ignore[var-annotated]

    vcs_provider = models.CharField(  # type: ignore[var-annotated]
        max_length=50,
        choices=VCSProvider.choices,
        default=VCSProvider.GITHUB,  # TODO: Remove when adding other providers
    )
    revision = models.CharField(max_length=100)  # type: ignore[var-annotated]
    code_references = models.JSONField[list[JSONCodeReference]](default=list)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # type: ignore[var-annotated]

    # Denormalised from code_references for efficient indexed lookups.
    # Populated automatically before save and kept in sorted order.
    feature_names = ArrayField(models.TextField(), default=list)  # type: ignore[var-annotated]

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["project", "repository_url", "-created_at"],
                name="code_ref_proj_repo_created_idx",
            ),
            GinIndex(
                fields=["feature_names"],
                name="code_refs_feat_names_gin_idx",
            ),
        ]

    @hook(BEFORE_SAVE)  # type: ignore[misc]
    def populate_feature_names(self) -> None:
        self.feature_names = sorted(
            {ref["feature_name"] for ref in self.code_references}
        )
