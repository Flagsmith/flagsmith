from task_processor.decorators import register_task_handler

from integrations.gitlab.models import GitLabConfiguration
from integrations.gitlab.services import (
    deregister_webhook_for_path,
    ensure_webhook_registered,
    has_live_resource_for_path,
)


@register_task_handler()
def register_gitlab_webhook(config_id: int, project_path: str) -> None:
    """Register a webhook for the GitLab project at ``project_path`` under this
    config. Dispatched at link time. Idempotent.
    """
    try:
        config = GitLabConfiguration.objects.get(
            id=config_id,
            deleted_at__isnull=True,
        )
    except GitLabConfiguration.DoesNotExist:
        return
    ensure_webhook_registered(config, project_path)


@register_task_handler()
def deregister_gitlab_webhook(config_id: int, project_path: str) -> None:
    """Deregister the webhook for ``project_path``. Dispatched at unlink time
    and from config destroy. No-op if the config is still active and any other
    linked resource in the same Flagsmith project still references this GitLab
    project.
    """
    config = GitLabConfiguration.objects.all_with_deleted().get(id=config_id)
    if config.deleted_at is None and has_live_resource_for_path(config, project_path):
        return
    deregister_webhook_for_path(config, project_path)
