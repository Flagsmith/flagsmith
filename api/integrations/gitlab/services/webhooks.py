import secrets
import uuid

import requests
import structlog
from django.urls import reverse

from core.helpers import get_current_site_url
from features.feature_external_resources.models import (
    GITLAB_RESOURCE_TYPES,
    FeatureExternalResource,
)
from integrations.gitlab.client import (
    create_project_hook,
    delete_project_hook,
)
from integrations.gitlab.models import GitLabConfiguration, GitLabWebhook
from integrations.gitlab.services.url_parsing import parse_project_path

logger = structlog.get_logger("gitlab")


def _get_webhook_url(webhook_uuid: uuid.UUID) -> str:
    path = reverse("api-v1:gitlab-webhook", kwargs={"webhook_uuid": str(webhook_uuid)})
    return f"{get_current_site_url()}{path}"


def has_live_resource_for_path(
    config: GitLabConfiguration,
    project_path: str,
) -> bool:
    """True if at least one live ``FeatureExternalResource`` under the config's
    project still references the given GitLab project path.
    """
    urls = FeatureExternalResource.objects.filter(
        feature__project=config.project,
        type__in=GITLAB_RESOURCE_TYPES,
    ).values_list("url", flat=True)
    return any(parse_project_path(url) == project_path for url in urls)


def register_gitlab_webhook_for_resource(resource: FeatureExternalResource) -> None:
    from integrations.gitlab.tasks import register_gitlab_webhook

    project_path = parse_project_path(resource.url)
    config = GitLabConfiguration.objects.filter(
        project=resource.feature.project,
    ).first()
    if config is not None and project_path is not None:
        register_gitlab_webhook.delay(args=(config.id, project_path))


def ensure_webhook_registered(
    config: GitLabConfiguration,
    project_path: str,
) -> GitLabWebhook:
    existing: GitLabWebhook | None = GitLabWebhook.objects.filter(
        gitlab_configuration=config,
        gitlab_path_with_namespace=project_path,
    ).first()
    if existing:
        return existing

    webhook_uuid = uuid.uuid4()
    secret = secrets.token_urlsafe(32)
    log = logger.bind(
        organisation__id=config.project.organisation_id,
        project__id=config.project_id,
    )
    try:
        hook = create_project_hook(
            instance_url=config.gitlab_instance_url,
            access_token=config.access_token,
            project_path=project_path,
            hook_url=_get_webhook_url(webhook_uuid),
            secret=secret,
        )
    except requests.RequestException as exc:
        log.error(
            "webhook.registration_failed",
            gitlab__project__path=project_path,
            exc_info=exc,
        )
        raise

    webhook: GitLabWebhook = GitLabWebhook.objects.create(
        uuid=webhook_uuid,
        gitlab_configuration=config,
        gitlab_project_id=hook["project_id"],
        gitlab_path_with_namespace=project_path,
        gitlab_hook_id=hook["id"],
        secret=secret,
    )
    log.info(
        "webhook.registered",
        gitlab__project__id=hook["project_id"],
        gitlab__project__path=project_path,
        gitlab__hook__id=hook["id"],
    )
    return webhook


def deregister_webhook_for_path(
    config: GitLabConfiguration,
    project_path: str,
) -> None:
    """Deregister the webhook previously registered for the given GitLab project
    path under this config, calling GitLab's DELETE endpoint and removing our
    local row. No-op if no webhook exists for that pair.
    """
    webhook = (
        GitLabWebhook.objects.all_with_deleted()
        .filter(
            gitlab_configuration=config,
            gitlab_path_with_namespace=project_path,
        )
        .first()
    )
    if webhook is None:
        return

    log = logger.bind(
        organisation__id=config.project.organisation_id,
        project__id=config.project_id,
    )
    try:
        delete_project_hook(
            instance_url=config.gitlab_instance_url,
            access_token=config.access_token,
            project_id=webhook.gitlab_project_id,
            hook_id=webhook.gitlab_hook_id,
        )
    except requests.RequestException as exc:
        log.warning(
            "webhook.deregistration_failed",
            gitlab__project__id=webhook.gitlab_project_id,
            gitlab__hook__id=webhook.gitlab_hook_id,
            exc_info=exc,
        )
    else:
        log.info(
            "webhook.deregistered",
            gitlab__project__id=webhook.gitlab_project_id,
            gitlab__hook__id=webhook.gitlab_hook_id,
        )
        webhook.delete()
