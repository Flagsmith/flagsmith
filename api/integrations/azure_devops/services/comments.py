import requests
import structlog
from django.db.models import Q
from django.template.loader import render_to_string

from core.helpers import get_current_site_url
from features.feature_external_resources.models import (
    AZURE_DEVOPS_RESOURCE_TYPES,
    FeatureExternalResource,
    ResourceType,
)
from features.models import Feature, FeatureState
from integrations.azure_devops.client import (
    add_pull_request_comment,
    add_work_item_comment,
)
from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.azure_devops.services.url_parsing import (
    parse_pull_request_url,
    parse_work_item_url,
)
from integrations.azure_devops.types import AzureDevOpsEnvironmentState

logger = structlog.get_logger("azure_devops")


def _post_to_resource(
    *,
    config: AzureDevOpsConfiguration,
    resource_url: str,
    resource_type: str,
    feature_id: int,
    body: str,
) -> None:
    """Parse an ADO resource URL and post the comment via the right
    endpoint. Used by every public function in this module.
    """
    if resource_type == ResourceType.AZURE_DEVOPS_PULL_REQUEST.value:
        ref = parse_pull_request_url(resource_url)
        if ref is None:
            return
        log = logger.bind(
            organisation__id=config.project.organisation_id,
            project__id=config.project_id,
            feature__id=feature_id,
            ado__project=ref.project,
            ado__resource__id=ref.pull_request_id,
        )
        try:
            add_pull_request_comment(
                organisation_url=config.organisation_url,
                pat=config.personal_access_token,
                project=ref.project,
                pull_request_id=ref.pull_request_id,
                body=body,
            )
        except requests.RequestException as exc:
            log.warning("comment.post_failed", exc_info=exc)
            return
        log.info("comment.posted")
        return

    if resource_type == ResourceType.AZURE_DEVOPS_WORK_ITEM.value:
        work_ref = parse_work_item_url(resource_url)
        if work_ref is None:
            return
        log = logger.bind(
            organisation__id=config.project.organisation_id,
            project__id=config.project_id,
            feature__id=feature_id,
            ado__project=work_ref.project,
            ado__resource__id=work_ref.work_item_id,
        )
        try:
            add_work_item_comment(
                organisation_url=config.organisation_url,
                pat=config.personal_access_token,
                project=work_ref.project,
                work_item_id=work_ref.work_item_id,
                body=body,
            )
        except requests.RequestException as exc:
            log.warning("comment.post_failed", exc_info=exc)
            return
        log.info("comment.posted")


def _get_environment_states(feature: Feature) -> list[AzureDevOpsEnvironmentState]:
    """Gather the current enabled state and value for ``feature`` across all
    environments in its project, suitable for rendering in a comment.
    """
    from environments.models import Environment

    site_url = get_current_site_url()
    environments = Environment.objects.filter(
        project=feature.project,
    ).order_by("id")

    states: list[AzureDevOpsEnvironmentState] = []
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
    """Post a comment on the linked ADO PR or work item showing the
    feature flag's current state across all environments. No-op when the
    project has no AzureDevOpsConfiguration.
    """
    try:
        config: AzureDevOpsConfiguration = AzureDevOpsConfiguration.objects.get(
            project=resource.feature.project,
        )
    except AzureDevOpsConfiguration.DoesNotExist:
        return

    feature = resource.feature
    environment_states = _get_environment_states(feature)
    body = render_to_string(
        "azure_devops/feature_linked_comment.md",
        {
            "feature_name": feature.name,
            "environment_states": environment_states,
        },
    )

    _post_to_resource(
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
    """Post a comment on the ADO resource informing that the feature flag
    has been unlinked.

    All parameters are passed explicitly because the
    ``FeatureExternalResource`` row no longer exists by the time this
    runs asynchronously.
    """
    try:
        config: AzureDevOpsConfiguration = AzureDevOpsConfiguration.objects.get(
            project_id=project_id,
        )
    except AzureDevOpsConfiguration.DoesNotExist:
        return

    body = render_to_string(
        "azure_devops/feature_unlinked_comment.md",
        {"feature_name": feature_name},
    )

    _post_to_resource(
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
    """Post a comment on every linked Azure DevOps resource informing that
    the feature flag has been deleted.

    All parameters are passed explicitly because the feature is being
    soft-deleted and may no longer be fully usable as an ORM object by
    the time this runs asynchronously.
    """
    try:
        config: AzureDevOpsConfiguration = AzureDevOpsConfiguration.objects.get(
            project_id=project_id,
        )
    except AzureDevOpsConfiguration.DoesNotExist:
        return

    resources = FeatureExternalResource.objects.filter(
        feature_id=feature_id,
        type__in=AZURE_DEVOPS_RESOURCE_TYPES,
    )
    if not resources.exists():
        return

    body = render_to_string(
        "azure_devops/feature_deleted_comment.md",
        {"feature_name": feature_name},
    )

    for resource in resources:
        _post_to_resource(
            config=config,
            resource_url=resource.url,
            resource_type=resource.type,
            feature_id=feature_id,
            body=body,
        )
