import re
from urllib.parse import urlsplit

import requests
import structlog
from rest_framework.exceptions import ValidationError

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from integrations.gitlab.client import (
    add_flagsmith_label_to_gitlab_issue,
    add_flagsmith_label_to_gitlab_merge_request,
    create_flagsmith_label,
    url_encode_gitlab_project_path,
)
from integrations.gitlab.models import GitLabConfiguration

logger = structlog.get_logger("gitlab")

_GITLAB_RESOURCE_PATH_PATTERN = re.compile(
    r"^/(?P<path>.+?)/-/(?:issues|work_items|merge_requests)/(?P<iid>\d+)/?$"
)


def apply_flagsmith_label_to_resource(
    resource: FeatureExternalResource,
) -> None:
    """
    Ensure the "Flagsmith Flag" label exists on the resource's GitLab project
    and apply it to the resource. No-op if tagging is disabled or unconfigured;
    raises ``ValidationError`` on parse/API failure (rolls back under atomic).
    """
    project = resource.feature.project
    config: GitLabConfiguration | None = GitLabConfiguration.objects.filter(
        project=project
    ).first()
    if not config or not config.tagging_enabled:
        return

    path_with_namespace, resource_iid = _parse_gitlab_resource_url(resource.url)
    gitlab_project = url_encode_gitlab_project_path(path_with_namespace)

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
            gitlab_project=gitlab_project,
        )
        if created:
            log.info("label.created")

        if resource.type == ResourceType.GITLAB_ISSUE:
            add_flagsmith_label_to_gitlab_issue(
                config.gitlab_instance_url,
                config.access_token,
                gitlab_project=gitlab_project,
                issue_iid=resource_iid,
            )
        else:
            add_flagsmith_label_to_gitlab_merge_request(
                config.gitlab_instance_url,
                config.access_token,
                gitlab_project=gitlab_project,
                merge_request_iid=resource_iid,
            )
        log.info("label.applied")
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


def _parse_gitlab_resource_url(url: str) -> tuple[str, int]:
    match = _GITLAB_RESOURCE_PATH_PATTERN.match(urlsplit(url).path)
    if not match:
        raise ValidationError({"url": "Could not parse GitLab resource URL."})
    return match["path"], int(match["iid"])
