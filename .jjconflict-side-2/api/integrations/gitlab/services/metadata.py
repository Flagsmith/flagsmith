import json

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

    for resource in resources:
        current = json.loads(resource.metadata) if resource.metadata else {}
        merged: GitLabResourceMetadata = {**current, **new_fields}
        changed = sorted(
            name for name, value in new_fields.items() if current.get(name) != value
        )
        if not changed:
            continue
        resource.metadata = json.dumps(merged)
        resource.save(update_fields=["metadata"])
