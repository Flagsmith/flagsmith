from django.db import transaction
from django.utils import timezone

from api_keys.user import APIKeyUser
from environments.models import Environment
from features.dependencies.services import (
    get_prerequisite_feature_names_by_environment,
    report_flag_dependencies,
    validate_feature_is_not_prerequisite,
)
from features.dependencies.types import FeatureName
from features.exceptions import FeatureNotFoundError
from features.feature_segments.mappers import (
    clears_legacy_flag_value,
    map_feature_state_data_to_segment_override,
)
from features.feature_segments.services import get_segment_override
from features.future.mappers import map_flag_value
from features.future.services import update_flag
from features.models import Feature, FeatureSegment, FeatureState
from features.tasks import trigger_feature_state_change_webhooks
from features.types import LegacyFeatureStateData
from integrations.github.constants import GitHubEventType
from integrations.github.github import call_github_task
from integrations.gitlab.services import (
    post_gitlab_state_change_comment_for_feature_state,
)
from users.models import FFAdminUser
from webhooks.webhooks import WebhookEventType


def get_feature(environment: Environment, feature_id: int) -> Feature:
    """Fetch a feature of the environment's project, or refuse with a 404."""
    try:
        return Feature.objects.get(  # type: ignore[no-any-return]
            id=feature_id, project_id=environment.project_id
        )
    except Feature.DoesNotExist:
        raise FeatureNotFoundError(feature_id) from None


def delete_feature(feature: Feature) -> None:
    """Delete the feature from every environment, or refuse with a 400."""
    with transaction.atomic():
        validate_feature_is_not_prerequisite(feature)
        _trigger_environment_defaults_deleted_webhooks(feature)
        prerequisite_feature_names_by_environment = (
            get_prerequisite_feature_names_by_environment(feature)
        )
        feature.delete()
    _report_prerequisites_lost(feature, prerequisite_feature_names_by_environment)


def _report_prerequisites_lost(
    feature: Feature,
    prerequisite_feature_names_by_environment: dict[Environment, set[FeatureName]],
) -> None:
    for environment, names in prerequisite_feature_names_by_environment.items():
        report_flag_dependencies(
            environment=environment, feature=feature, created=[], deleted=names
        )


def _trigger_environment_defaults_deleted_webhooks(feature: Feature) -> None:
    for feature_state in feature.feature_states.filter(
        identity=None, feature_segment=None
    ):
        trigger_feature_state_change_webhooks(
            feature_state, WebhookEventType.FLAG_DELETED
        )


def notify_code_references_of_feature_state(feature_state: FeatureState) -> None:
    """Comment on the issues and pull requests linked to the feature."""
    if (
        not feature_state.identity_id
        and feature_state.feature.external_resources.exists()
        and feature_state.environment.project.github_project.exists()  # type: ignore[union-attr]
        and feature_state.environment.project.organisation.github_config.exists()  # type: ignore[union-attr]
    ):
        call_github_task(
            organisation_id=feature_state.feature.project.organisation_id,
            type=GitHubEventType.FLAG_UPDATED.value,
            feature=feature_state.feature,
            segment_name=None,
            url=None,
            feature_states=[feature_state],
        )
    post_gitlab_state_change_comment_for_feature_state(feature_state)


def writes_live_segment_override(feature_state_data: LegacyFeatureStateData) -> bool:
    """Whether feature state data, validated by a legacy API, is for a live override.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """
    live_from = feature_state_data.get("live_from")
    return not (
        feature_state_data.get("identity")
        or feature_state_data.get("environment_feature_version")
        or feature_state_data.get("change_request")
        or (live_from and live_from > timezone.now())
    )


def write_segment_override(
    *,
    environment: Environment,
    feature: Feature,
    segment_id: int,
    feature_state_data: LegacyFeatureStateData,
    author: FFAdminUser | APIKeyUser,
    priority: int | None = None,
) -> FeatureState:
    """Write a live override through the flag API, from data validated by a
    legacy API.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """
    with transaction.atomic():
        update_flag(
            environment=environment,
            feature=feature,
            changes={
                "segment_overrides": [
                    map_feature_state_data_to_segment_override(
                        segment_id, feature_state_data, priority=priority
                    )
                ]
            },
            replace=False,
            author=author,
            system=False,
        )
        feature_state = get_segment_override(
            environment=environment, feature=feature, segment_id=segment_id
        )
        assert feature_state is not None
        feature_state_value = feature_state.feature_state_value
        if clears_legacy_flag_value(feature_state_data) and (
            map_flag_value(feature_state_value) is not None
        ):
            # Legacy APIs write overrides directly only without v2 feature
            # versioning, so clearing values in place doesn't bypass it.
            feature_state_value.string_value = None
            feature_state_value.integer_value = None
            feature_state_value.boolean_value = None
            feature_state_value.save()
    return feature_state


def write_live_segment_override(
    feature_segment: FeatureSegment,
    feature_state_data: LegacyFeatureStateData,
    *,
    author: FFAdminUser | APIKeyUser,
) -> FeatureState:
    """Write a live override through the flag API, from data validated by the
    legacy feature state API, notifying linked issues and pull requests.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """
    feature_state = write_segment_override(
        environment=feature_segment.environment,
        feature=feature_segment.feature,
        segment_id=feature_segment.segment_id,
        feature_state_data=feature_state_data,
        author=author,
    )
    notify_code_references_of_feature_state(feature_state)
    return feature_state


def is_segment_override_unchanged(
    feature_segment: FeatureSegment,
    feature_state: FeatureState,
    feature_state_data: LegacyFeatureStateData,
) -> bool:
    """Whether writing data, validated by a legacy API, leaves an override as it is.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """
    changes = map_feature_state_data_to_segment_override(
        feature_segment.segment_id, feature_state_data
    )
    value = map_flag_value(feature_state.feature_state_value)
    weights = {
        multivariate_value.multivariate_feature_option_id: (
            multivariate_value.percentage_allocation
        )
        for multivariate_value in feature_state.multivariate_feature_state_values.all()
    }
    new_value = (
        None
        if clears_legacy_flag_value(feature_state_data)
        else changes.get("value", value)
    )
    return (
        changes.get("enabled", feature_state.enabled) == feature_state.enabled
        and new_value == value
        and all(
            weights.get(variant["id"]) == variant["weight"]
            for variant in changes.get("variants", [])
        )
    )
