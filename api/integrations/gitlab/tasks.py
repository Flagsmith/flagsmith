import requests
import structlog
from task_processor.decorators import register_task_handler

from features.feature_external_resources.models import FeatureExternalResource
from features.models import FeatureState
from integrations.gitlab.client import remove_flagsmith_label_from_gitlab_resource
from integrations.gitlab.models import GitLabConfiguration
from integrations.gitlab.services import (
    deregister_webhook_for_path,
    ensure_webhook_registered,
    has_live_resource_for_path,
    post_feature_deleted_comment,
    post_linked_comment,
    post_state_change_comment,
    post_unlinked_comment,
)
from integrations.gitlab.services.labels import (
    GITLAB_RESOURCE_KIND_BY_TYPE,
    apply_flagsmith_label_to_resource,
)
from integrations.gitlab.services.url_parsing import (
    parse_project_path,
    parse_resource_iid,
)

logger = structlog.get_logger("gitlab")


@register_task_handler()
def register_gitlab_webhook(
    config_id: int,
    project_path: str,
    api_base_url: str,
) -> None:
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
    ensure_webhook_registered(config, project_path, api_base_url=api_base_url)


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


@register_task_handler()
def post_gitlab_linked_comment(resource_id: int) -> None:
    """Post a comment on the linked GitLab resource showing the feature flag's
    current state. Dispatched at link time.
    """
    try:
        resource = FeatureExternalResource.objects.get(id=resource_id)
    except FeatureExternalResource.DoesNotExist:
        return
    post_linked_comment(resource)


@register_task_handler()
def post_gitlab_unlinked_comment(
    feature_name: str,
    feature_id: int,
    resource_url: str,
    resource_type: str,
    project_id: int,
) -> None:
    """Post a comment on the GitLab resource informing that the feature flag
    has been unlinked.  Dispatched at unlink time.  All data is passed
    directly because the resource row no longer exists.
    """
    post_unlinked_comment(
        feature_name=feature_name,
        feature_id=feature_id,
        resource_url=resource_url,
        resource_type=resource_type,
        project_id=project_id,
    )


@register_task_handler()
def post_gitlab_state_change_comment(feature_state_id: int) -> None:
    """Post a comment on every linked GitLab resource when a feature flag's
    state changes.  Dispatched from the feature-state serialiser save hook.
    """
    try:
        feature_state = FeatureState.objects.select_related(
            "feature",
            "environment",
            "feature_segment__segment",
            "feature__project",
            "identity",
        ).get(id=feature_state_id)
    except FeatureState.DoesNotExist:
        return
    post_state_change_comment(feature_state)


@register_task_handler()
def post_gitlab_feature_deleted_comment(
    feature_name: str,
    feature_id: int,
    project_id: int,
) -> None:
    """Post a comment on every linked GitLab resource informing that the
    feature flag has been deleted.  Dispatched from the Feature model
    soft-delete hook.
    """
    post_feature_deleted_comment(
        feature_name=feature_name,
        feature_id=feature_id,
        project_id=project_id,
    )


@register_task_handler()
def apply_gitlab_label(resource_id: int) -> None:
    """Apply the "Flagsmith Feature" label to the linked GitLab resource.
    Dispatched at link time.  No-op if labelling is disabled or unconfigured.
    """
    try:
        resource = FeatureExternalResource.objects.get(id=resource_id)
    except FeatureExternalResource.DoesNotExist:
        return
    apply_flagsmith_label_to_resource(resource)


@register_task_handler()
def remove_gitlab_label(
    *,
    project_id: int,
    feature_id: int,
    resource_pk: int,
    resource_url: str,
    resource_type: str,
) -> None:
    """Remove the "Flagsmith Feature" label from a GitLab issue/MR.
    No-op if another FeatureExternalResource still references the same URL.
    """
    config: GitLabConfiguration | None = GitLabConfiguration.objects.filter(
        project_id=project_id
    ).first()
    if not config or not config.labeling_enabled:
        return
    if (
        FeatureExternalResource.objects.filter(url=resource_url)
        .exclude(pk=resource_pk)
        .exists()
    ):
        return

    path_with_namespace = parse_project_path(resource_url)
    resource_iid = parse_resource_iid(resource_url)
    if path_with_namespace is None or resource_iid is None:
        return

    log = logger.bind(
        project__id=project_id,
        feature__id=feature_id,
        gitlab_project__path=path_with_namespace,
        resource__type=resource_type,
        resource__iid=resource_iid,
    )

    try:
        remove_flagsmith_label_from_gitlab_resource(
            config.gitlab_instance_url,
            config.access_token,
            project_path=path_with_namespace,
            resource_kind=GITLAB_RESOURCE_KIND_BY_TYPE[resource_type],
            resource_iid=resource_iid,
        )
        log.info("label.removed")
    except requests.RequestException:
        log.exception("label.removal_failed")
