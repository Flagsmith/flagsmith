from task_processor.decorators import register_task_handler

from features.feature_external_resources.models import (
    GITLAB_RESOURCE_TYPES,
    FeatureExternalResource,
)
from integrations.gitlab.models import GitLabConfiguration
from integrations.gitlab.services import (
    deregister_webhooks,
    register_webhook_for_resource,
)


@register_task_handler()
def register_gitlab_webhooks(config_id: int) -> None:
    """Register GitLab webhooks for each distinct external resource URL
    already linked to this config's Flagsmith project. Best-effort backfill —
    task processor handles retries/logging on failure.
    """

    config = GitLabConfiguration.objects.get(
        id=config_id,
        deleted_at__isnull=True,
    )

    urls = set(
        FeatureExternalResource.objects.filter(
            feature__project=config.project,
            type__in=GITLAB_RESOURCE_TYPES,
        ).values_list("url", flat=True)
    )
    for url in urls:
        register_webhook_for_resource(config=config, resource_url=url)


@register_task_handler()
def deregister_gitlab_webhooks(config_id: int) -> None:
    """Deregister every webhook previously registered under this config.
    Runs after the config has been soft-deleted, so the lookup includes
    soft-deleted rows.
    """
    config = GitLabConfiguration.objects.all_with_deleted().get(id=config_id)
    deregister_webhooks(config)
