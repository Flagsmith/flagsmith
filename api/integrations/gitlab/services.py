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
from integrations.gitlab.exceptions import GitLabApiUnreachable
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


def _get_webhook_url(webhook_uuid: uuid.UUID) -> str:
    path = reverse("api-v1:gitlab-webhook", kwargs={"webhook_uuid": str(webhook_uuid)})
    return f"{get_current_site_url()}{path}"


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


def register_webhook_for_resource(
    config: GitLabConfiguration,
    resource_url: str | None,
) -> None:
    """Register a webhook for the GitLab project referenced by ``resource_url``.

    No-op if the URL doesn't parse as a GitLab issue/MR. Raises
    :class:`GitLabApiUnreachable` (503) when the call to GitLab fails — the
    failure is logged before re-raising.
    """
    match = _RESOURCE_PATH_PATTERN.match(urlparse(resource_url or "").path)
    if not match:
        return
    try:
        ensure_webhook_registered(config, match.group("path"))
    except requests.RequestException as exc:
        raise GitLabApiUnreachable() from exc


def deregister_webhooks(config: GitLabConfiguration) -> None:
    log = logger.bind(
        organisation__id=config.project.organisation_id,
        project__id=config.project_id,
    )
    webhooks = GitLabWebhook.objects.all_with_deleted().filter(
        gitlab_configuration=config,
    )
    for webhook in webhooks:
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
            external_resources__url=resource_url,
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
