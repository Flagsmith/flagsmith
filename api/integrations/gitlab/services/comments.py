import requests
import structlog
from django.db.models import Q
from django.template.loader import render_to_string

from core.helpers import get_current_site_url
from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from features.models import Feature, FeatureState
from integrations.gitlab.client import (
    create_issue_note,
    create_merge_request_note,
)
from integrations.gitlab.models import GitLabConfiguration
from integrations.gitlab.services.url_parsing import (
    parse_project_path,
    parse_resource_iid,
)
from integrations.gitlab.types import GitLabEnvironmentState

logger = structlog.get_logger("gitlab")


def _get_environment_states(
    feature: Feature,
) -> list[GitLabEnvironmentState]:
    """Gather the current enabled state and value for ``feature`` across all
    environments in its project, suitable for rendering in a comment.
    """
    from environments.models import Environment

    site_url = get_current_site_url()
    environments = Environment.objects.filter(
        project=feature.project,
    ).order_by("id")

    states: list[GitLabEnvironmentState] = []
    for environment in environments:
        feature_state: FeatureState | None = (
            FeatureState.objects.get_live_feature_states(
                environment=environment,
                additional_filters=Q(
                    feature=feature,
                    identity__isnull=True,
                    feature_segment__isnull=True,
                ),
            ).first()
        )
        if feature_state is None:
            continue

        value = feature_state.get_feature_state_value()
        env_url = (
            f"{site_url}/project/{feature.project_id}"
            f"/environment/{environment.api_key}"
            f"/features?feature={feature.id}"
        )
        states.append(
            {
                "name": environment.name,
                "url": env_url,
                "enabled": feature_state.enabled,
                "value": value if value not in (None, "") else None,
            }
        )
    return states


def post_linked_comment(resource: FeatureExternalResource) -> None:
    """Post a comment on the linked GitLab issue or merge request showing the
    feature flag's current state across all environments.
    """
    try:
        config: GitLabConfiguration = GitLabConfiguration.objects.get(
            project=resource.feature.project,
        )
    except GitLabConfiguration.DoesNotExist:
        return

    if (project_path := parse_project_path(resource.url)) is None:
        return

    if (iid := parse_resource_iid(resource.url)) is None:
        return

    feature = resource.feature
    environment_states = _get_environment_states(feature)
    body = render_to_string(
        "gitlab/feature_linked_comment.md",
        {
            "feature_name": feature.name,
            "environment_states": environment_states,
        },
    )

    log = logger.bind(
        organisation__id=config.project.organisation_id,
        project__id=config.project_id,
        feature__id=feature.id,
        gitlab__project__path=project_path,
        gitlab__resource__iid=iid,
    )

    try:
        if resource.type == ResourceType.GITLAB_ISSUE:
            create_issue_note(
                instance_url=config.gitlab_instance_url,
                access_token=config.access_token,
                project_path=project_path,
                issue_iid=iid,
                body=body,
            )
        elif resource.type == ResourceType.GITLAB_MR:
            create_merge_request_note(
                instance_url=config.gitlab_instance_url,
                access_token=config.access_token,
                project_path=project_path,
                merge_request_iid=iid,
                body=body,
            )
        else:
            return
    except requests.RequestException as exc:
        log.warning("comment.post_failed", exc_info=exc)
    else:
        log.info("comment.posted")
