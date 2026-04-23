from typing import Literal

import requests
import structlog
from rest_framework.exceptions import ValidationError

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from integrations.gitlab.client import (
    add_flagsmith_label_to_gitlab_resource,
    create_flagsmith_label,
)
from integrations.gitlab.models import GitLabConfiguration

logger = structlog.get_logger("gitlab")

GitLabResourceKind = Literal["issues", "merge_requests"]

GITLAB_RESOURCE_KIND_BY_TYPE: dict[str, GitLabResourceKind] = {
    ResourceType.GITLAB_ISSUE.value: "issues",
    ResourceType.GITLAB_MR.value: "merge_requests",
}


def apply_flagsmith_label_to_resource(
    resource: FeatureExternalResource,
) -> None:
    """Ensure the "Flagsmith Flag" label exists on the resource's GitLab project
    and apply it to the resource. No-op if labeling is disabled or unconfigured;
    raises ``ValidationError`` on parse/API failure (rolls back under atomic).
    """
    from integrations.gitlab.services import parse_project_path, parse_resource_iid

    project = resource.feature.project
    config: GitLabConfiguration | None = GitLabConfiguration.objects.filter(
        project=project
    ).first()
    if not config or not config.labeling_enabled:
        return

    path_with_namespace = parse_project_path(resource.url)
    resource_iid = parse_resource_iid(resource.url)
    if path_with_namespace is None or resource_iid is None:
        raise ValidationError({"url": "Could not parse GitLab resource URL."})

    log = logger.bind(
        organisation__id=project.organisation_id,
        project__id=project.id,
        feature__id=resource.feature_id,
        gitlab_project__path=path_with_namespace,
        resource__type=resource.type,
        resource__iid=resource_iid,
    )

    try:
        created = create_flagsmith_label(
            config.gitlab_instance_url,
            config.access_token,
            project_path=path_with_namespace,
        )
        if created:
            log.info("label.created")

        add_flagsmith_label_to_gitlab_resource(
            config.gitlab_instance_url,
            config.access_token,
            project_path=path_with_namespace,
            resource_kind=GITLAB_RESOURCE_KIND_BY_TYPE[resource.type],
            resource_iid=resource_iid,
        )
    except requests.RequestException as exc:
        log.exception("label.failed")
        raise ValidationError(
            {
                "detail": (
                    "Failed to apply the Flagsmith Flag label on GitLab. "
                    "Check the GitLab access token's permissions and try again."
                ),
            },
        ) from exc
