import requests
import structlog
from django.db.models import Q
from django.template.loader import render_to_string

from core.helpers import get_current_site_url
from features.feature_external_resources.models import (
    GITLAB_RESOURCE_TYPES,
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


def _post_note_to_resource(
    *,
    config: GitLabConfiguration,
    resource_url: str,
    resource_type: str,
    feature_id: int,
    body: str,
) -> None:
    """Parse a GitLab resource URL, post a note via the API, and log the
    outcome.  Shared by every comment-posting function in this module.
    """
    project_path = parse_project_path(resource_url)
    iid = parse_resource_iid(resource_url)
    if project_path is None or iid is None:
        return

    log = logger.bind(
        organisation__id=config.project.organisation_id,
        project__id=config.project_id,
        feature__id=feature_id,
        gitlab__project__path=project_path,
        gitlab__resource__iid=iid,
    )

    try:
        if resource_type == ResourceType.GITLAB_ISSUE:
            create_issue_note(
                instance_url=config.gitlab_instance_url,
                access_token=config.access_token,
                project_path=project_path,
                issue_iid=iid,
                body=body,
            )
        elif resource_type == ResourceType.GITLAB_MR:
            create_merge_request_note(
                instance_url=config.gitlab_instance_url,
                access_token=config.access_token,
                project_path=project_path,
                merge_request_iid=iid,
                body=body,
            )
    except requests.RequestException as exc:
        log.warning("comment.post_failed", exc_info=exc)
    else:
        log.info("comment.posted")


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
            continue  # pragma: no cover — initial states are always created

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

    feature = resource.feature
    environment_states = _get_environment_states(feature)
    body = render_to_string(
        "gitlab/feature_linked_comment.md",
        {
            "feature_name": feature.name,
            "environment_states": environment_states,
        },
    )

    _post_note_to_resource(
        config=config,
        resource_url=resource.url,
        resource_type=resource.type,
        feature_id=feature.id,
        body=body,
    )


def post_unlinked_comment(
    feature_name: str,
    feature_id: int,
    resource_url: str,
    resource_type: str,
    project_id: int,
) -> None:
    """Post a comment on the GitLab issue or merge request informing that the
    feature flag has been unlinked.

    All parameters are passed explicitly because the
    ``FeatureExternalResource`` row no longer exists by the time this runs.
    """
    try:
        config: GitLabConfiguration = GitLabConfiguration.objects.get(
            project_id=project_id,
        )
    except GitLabConfiguration.DoesNotExist:
        return

    body = render_to_string(
        "gitlab/feature_unlinked_comment.md",
        {"feature_name": feature_name},
    )

    _post_note_to_resource(
        config=config,
        resource_url=resource_url,
        resource_type=resource_type,
        feature_id=feature_id,
        body=body,
    )


def post_feature_deleted_comment(
    feature_name: str,
    feature_id: int,
    project_id: int,
) -> None:
    """Post a comment on every linked GitLab resource informing that the
    feature flag has been deleted.

    All parameters are passed explicitly because the feature is being
    soft-deleted and may no longer be fully usable as an ORM object by the
    time this runs asynchronously.
    """
    try:
        config: GitLabConfiguration = GitLabConfiguration.objects.get(
            project_id=project_id,
        )
    except GitLabConfiguration.DoesNotExist:
        return

    resources = FeatureExternalResource.objects.filter(
        feature_id=feature_id,
        type__in=GITLAB_RESOURCE_TYPES,
    )
    if not resources.exists():
        return

    body = render_to_string(
        "gitlab/feature_deleted_comment.md",
        {"feature_name": feature_name},
    )

    for resource in resources:
        _post_note_to_resource(
            config=config,
            resource_url=resource.url,
            resource_type=resource.type,
            feature_id=feature_id,
            body=body,
        )


def post_gitlab_state_change_comment_for_feature_state(
    feature_state: FeatureState,
) -> None:
    """Dispatch a state-change comment task for `feature_state` when the
    project has a GitLab integration configured. No-op otherwise so projects
    without GitLab don't pay for a queue entry and a `GitLabConfiguration`
    lookup per feature-state save.
    """
    from integrations.gitlab.tasks import post_gitlab_state_change_comment

    if not feature_state.environment:
        return
    if not hasattr(feature_state.environment.project, "gitlab_config"):
        return
    post_gitlab_state_change_comment.delay(args=(feature_state.id,))


def post_state_change_comment(feature_state: FeatureState) -> None:
    """Post a comment on every linked GitLab resource when a feature flag's
    state changes, covering environment-level, segment override, and identity
    override scopes.
    """
    feature = feature_state.feature

    try:
        config: GitLabConfiguration = GitLabConfiguration.objects.get(
            project=feature.project,
        )
    except GitLabConfiguration.DoesNotExist:
        return

    resources = feature.external_resources.filter(type__in=GITLAB_RESOURCE_TYPES)
    if not resources.exists():
        return

    environment = feature_state.environment
    if environment is None:
        return

    if feature_state.feature_segment_id is not None:
        feature_segment = feature_state.feature_segment
        scope = "segment"
        scope_name: str | None = (
            feature_segment.segment.name if feature_segment else None
        )
    elif feature_state.identity_id is not None:
        identity = feature_state.identity
        scope = "identity"
        scope_name = identity.identifier if identity else None
    else:
        scope = "environment"
        scope_name = None

    value = feature_state.get_feature_state_value()
    body = render_to_string(
        "gitlab/feature_state_changed_comment.md",
        {
            "feature_name": feature.name,
            "environment_name": environment.name,
            "enabled": feature_state.enabled,
            "value": value if value not in (None, "") else None,
            "scope": scope,
            "scope_name": scope_name,
        },
    )

    for resource in resources:
        _post_note_to_resource(
            config=config,
            resource_url=resource.url,
            resource_type=resource.type,
            feature_id=feature.id,
            body=body,
        )
