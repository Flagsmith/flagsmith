import structlog

from features.feature_external_resources.models import (
    GITLAB_RESOURCE_TYPES,
    FeatureExternalResource,
)
from features.models import Feature
from integrations.gitlab.constants import (
    GITLAB_TAG_COLOR,
    GITLAB_TAG_DESCRIPTION_BY_LABEL,
    GITLAB_TAG_KIND_BY_LABEL,
    GITLAB_TAG_KIND_BY_RESOURCE_TYPE,
    GitLabTagLabel,
)
from integrations.gitlab.mappers import (
    map_gitlab_resource_to_tag_label,
    map_gitlab_webhook_payload_to_tag_label,
    map_resource_url_to_filter_value,
)
from integrations.gitlab.models import GitLabWebhook
from integrations.gitlab.types import GitLabWebhookPayload
from projects.tags.models import Tag, TagType

logger = structlog.get_logger("gitlab")


def set_gitlab_tag(feature: Feature, new_label: GitLabTagLabel) -> None:
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
            external_resources__url__in=map_resource_url_to_filter_value(resource_url),
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


def clear_tag_for_resource(resource: FeatureExternalResource) -> None:
    """Remove the GitLab tag for `resource`'s kind (Issue/MR) from its
    feature when no other linked `FeatureExternalResource` of the same
    kind remains. Safe to call whether `resource` is still in the DB or
    has already been deleted.
    """
    kind = GITLAB_TAG_KIND_BY_RESOURCE_TYPE.get(resource.type)
    if kind is None:
        return
    if (
        FeatureExternalResource.objects.filter(
            feature=resource.feature,
            type=resource.type,
        )
        .exclude(pk=resource.pk)
        .exists()
    ):
        return
    resource.feature.tags.remove(
        *resource.feature.tags.filter(
            type=TagType.GITLAB.value,
            label__startswith=kind,
        )
    )
