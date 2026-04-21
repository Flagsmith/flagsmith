import re
import secrets
import uuid
from typing import Any
from urllib.parse import urlparse

import requests
import structlog
from django.urls import reverse

from core.helpers import get_current_site_url
from features.feature_external_resources.models import (
    GITLAB_RESOURCE_TYPES,
    FeatureExternalResource,
)
from features.models import Feature
from integrations.gitlab.client import (
    create_project_hook,
    delete_project_hook,
)
from integrations.gitlab.constants import (
    GITLAB_TAG_COLOR,
    GITLAB_TAG_DESCRIPTION_BY_LABEL,
    GITLAB_TAG_KIND_BY_LABEL,
    GitLabTagLabel,
)
from integrations.gitlab.mappers import (
    map_gitlab_resource_to_tag_label,
    map_gitlab_webhook_payload_to_tag_label,
)
from integrations.gitlab.models import GitLabConfiguration, GitLabWebhook
from integrations.gitlab.types import GitLabWebhookPayload
from projects.tags.models import Tag, TagType

logger = structlog.get_logger("gitlab")

_RESOURCE_PATH_PATTERN = re.compile(
    r"^/(?P<path>.+?)/-/(?:issues|work_items|merge_requests)/\d+/?$"
)


def parse_project_path(resource_url: str | None) -> str | None:
    """Return the GitLab project's URL-encodable path (``group/subgroup/project``)
    from an issue or MR URL, or ``None`` if the URL isn't in the expected shape.
    """
    if not resource_url:
        return None
    match = _RESOURCE_PATH_PATTERN.match(urlparse(resource_url).path)
    return match.group("path") if match else None


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


def set_gitlab_tag(feature: Any, new_label: GitLabTagLabel) -> None:
    """Apply a GitLab system tag to ``feature``, replacing any existing GitLab
    tag of the same kind (Issue/MR) first. Issue tags and MR tags coexist
    independently — an Issue event won't touch an MR tag or vice versa.
    """
    label_value = new_label.value

    feature.tags.remove(
        *feature.tags.filter(
            type=TagType.GITLAB.value,
            label__startswith=GITLAB_TAG_KIND_BY_LABEL[new_label],
        )
    )
    tag, _ = Tag.objects.get_or_create(
        label=label_value,
        project=feature.project,
        is_system_tag=True,
        type=TagType.GITLAB.value,
        defaults={
            "color": GITLAB_TAG_COLOR,
            "description": GITLAB_TAG_DESCRIPTION_BY_LABEL[new_label],
        },
    )
    feature.tags.add(tag)


def apply_initial_tag(resource: FeatureExternalResource) -> None:
    """Tag `resource.feature` based on the linked GitLab issue/MR's state
    at link time.
    """
    label = map_gitlab_resource_to_tag_label(resource)
    if not label:
        return
    set_gitlab_tag(resource.feature, label)


def _issue_url_variants(url: str) -> list[str]:
    """GitLab delivers issue webhooks with ``/-/work_items/<iid>`` URLs even when
    the feature was linked via the legacy ``/-/issues/<iid>`` form (and vice
    versa). Return both shapes so the matcher finds the stored resource.
    """
    if "/-/issues/" in url:
        return [url, url.replace("/-/issues/", "/-/work_items/", 1)]
    if "/-/work_items/" in url:
        return [url, url.replace("/-/work_items/", "/-/issues/", 1)]
    return [url]


def apply_tag_for_event(
    webhook: GitLabWebhook,
    payload: GitLabWebhookPayload,
) -> None:
    if not (label := map_gitlab_webhook_payload_to_tag_label(payload)):
        return

    if not (
        resource_url := (attrs := payload.get("object_attributes") or {}).get("url")
    ):
        return

    if not (
        feature := Feature.objects.filter(
            project=webhook.gitlab_configuration.project,
            external_resources__url__in=_issue_url_variants(resource_url),
            external_resources__type__in=GITLAB_RESOURCE_TYPES,
        ).first()
    ):
        return

    set_gitlab_tag(feature, label)
    log = logger.bind(
        organisation__id=webhook.gitlab_configuration.project.organisation_id,
        project__id=webhook.gitlab_configuration.project_id,
    )
    log.info(
        "feature.tagged",
        feature__id=feature.id,
        tag__label=label.value,
        object_kind=payload.get("object_kind"),
        action=attrs.get("action"),
    )
