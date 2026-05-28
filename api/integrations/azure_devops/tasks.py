import structlog
from task_processor.decorators import register_task_handler

from features.feature_external_resources.models import FeatureExternalResource
from features.models import FeatureState
from integrations.azure_devops.services.comments import (
    post_feature_deleted_comment,
    post_linked_comment,
    post_state_change_comment,
    post_unlinked_comment,
)

logger = structlog.get_logger("azure_devops")


@register_task_handler()
def post_azure_devops_linked_comment(resource_id: int) -> None:
    """Post a comment on the linked Azure DevOps resource showing the
    feature flag's current state. Dispatched at link time.
    """
    try:
        resource = FeatureExternalResource.objects.get(id=resource_id)
    except FeatureExternalResource.DoesNotExist:
        return
    post_linked_comment(resource)


@register_task_handler()
def post_azure_devops_unlinked_comment(
    feature_name: str,
    feature_id: int,
    resource_url: str,
    resource_type: str,
    project_id: int,
) -> None:
    """Post a comment on the ADO resource informing that the feature flag
    has been unlinked. Dispatched at unlink time. All data is passed
    directly because the resource row no longer exists.
    """
    post_unlinked_comment(
        feature_name=feature_name,
        feature_id=feature_id,
        resource_url=resource_url,
        resource_type=resource_type,
        project_id=project_id,
    )


@register_task_handler()
def post_azure_devops_state_change_comment(feature_state_id: int) -> None:
    """Post a comment on every linked Azure DevOps resource when a feature
    flag's state changes. Dispatched from the feature-state save hook.
    """
    try:
        feature_state = FeatureState.objects.select_related(
            "feature",
            "environment",
            "feature_segment__segment",
            "feature__project",
            "identity",
        ).get(id=feature_state_id)
    except FeatureState.DoesNotExist:
        return
    post_state_change_comment(feature_state)


@register_task_handler()
def post_azure_devops_feature_deleted_comment(
    feature_name: str,
    feature_id: int,
    project_id: int,
) -> None:
    """Post a comment on every linked Azure DevOps resource informing that
    the feature flag has been deleted. Dispatched from the Feature
    soft-delete hook.
    """
    post_feature_deleted_comment(
        feature_name=feature_name,
        feature_id=feature_id,
        project_id=project_id,
    )
