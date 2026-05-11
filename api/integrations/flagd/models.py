"""
Per-project enablement for the flagd integration.

The sync and diagnostics endpoints are gated on a row in this table
existing with ``enabled=True``. Default state for any project is
"integration off" — the new endpoints do not respond until an
operator (or the ``bootstrap_flagd_local`` command) enables them.

Kept deliberately thin: a single boolean alongside ownership of which
project it applies to. Future fields (rate limits, custom translator
options, etc.) can be added without disturbing the gating contract.
"""

from __future__ import annotations

from django.db import models

from projects.models import Project


class FlagdProjectConfiguration(models.Model):
    project = models.OneToOneField(
        Project,
        related_name="flagd_configuration",
        on_delete=models.CASCADE,
    )
    enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "flagd project configuration"
        verbose_name_plural = "flagd project configurations"

    def __str__(self) -> str:
        state = "enabled" if self.enabled else "disabled"
        return f"flagd integration for project {self.project_id} ({state})"


def is_flagd_enabled_for_project(project_id: int) -> bool:
    """
    Cheap lookup used by the sync/diagnostics endpoint guards. Returns
    ``False`` when no configuration row exists for the project (the
    opt-in default).
    """
    return FlagdProjectConfiguration.objects.filter(
        project_id=project_id, enabled=True
    ).exists()
