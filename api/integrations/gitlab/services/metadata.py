import json

import structlog

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from integrations.gitlab.mappers import (
    map_gitlab_webhook_payload_to_resource_metadata,
    map_resource_url_to_filter_value,
)
from integrations.gitlab.models import GitLabWebhook
from integrations.gitlab.types import GitLabResourceMetadata, GitLabWebhookPayload

logger = structlog.get_logger("gitlab")

_RESOURCE_TYPE_BY_OBJECT_KIND: dict[str, str] = {
    "issue": ResourceType.GITLAB_ISSUE.value,
    "merge_request": ResourceType.GITLAB_MR.value,
}


def update_resource_metadata(
    webhook: GitLabWebhook,
    payload: GitLabWebhookPayload,
) -> None:
    new_fields = map_gitlab_webhook_payload_to_resource_metadata(payload)
    resource_type = _RESOURCE_TYPE_BY_OBJECT_KIND.get(payload.get("object_kind") or "")
    resource_url = (payload.get("object_attributes") or {}).get("url")
    if not (new_fields and resource_type and resource_url):
        return

    resources = FeatureExternalResource.objects.filter(
        feature__project=webhook.gitlab_configuration.project,
        type=resource_type,
        url__in=map_resource_url_to_filter_value(resource_url),
    )

    log = logger.bind(
        organisation__id=webhook.gitlab_configuration.project.organisation_id,
        project__id=webhook.gitlab_configuration.project_id,
    )
    for resource in resources:
        current = json.loads(resource.metadata) if resource.metadata else {}
        merged: GitLabResourceMetadata = {**current, **new_fields}
        if merged == current:
            continue
        resource.metadata = json.dumps(merged)
        resource.save(update_fields=["metadata"])
        log.info(
            "external_resource.metadata.refreshed",
            feature__id=resource.feature_id,
            external_resource__id=resource.id,
            object_kind=payload.get("object_kind"),
            state=merged.get("state"),
        )
