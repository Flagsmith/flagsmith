import json
from datetime import timedelta
from typing import Optional, Union

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from environments.models import Environment
from features.models import Feature, FeatureStateValue
from features.multivariate.models import MultivariateFeatureOption
from features.value_types import BOOLEAN, INTEGER, STRING
from features.versioning.versioning_service import get_environment_flags_list
from projects.models import Project
from task_processor.decorators import (
    register_recurring_task,
    register_task_handler,
)

from .constants import FAILED, OVERWRITE_DESTRUCTIVE, PROCESSING, SKIP, SUCCESS
from .models import (
    FeatureExport,
    FeatureImport,
    FlagsmithOnFlagsmithFeatureExport,
)


@register_recurring_task(
    run_every=timedelta(hours=12),
)
def clear_stale_feature_imports_and_exports() -> None:
    two_weeks_ago = timezone.now() - timedelta(days=14)
    FeatureExport.objects.filter(created_at__lt=two_weeks_ago).delete()
    FeatureImport.objects.filter(created_at__lt=two_weeks_ago).delete()


@register_recurring_task(
    run_every=timedelta(minutes=10),
)
def retire_stalled_feature_imports_and_exports() -> None:
    ten_minutes_ago = timezone.now() - timedelta(minutes=10)

    feature_exports = []
    for feature_export in FeatureExport.objects.filter(
        created_at__lt=ten_minutes_ago,
        status=PROCESSING,
    ):
        feature_export.status = FAILED
        feature_exports.append(feature_export)
    FeatureExport.objects.bulk_update(feature_exports, ["status"])

    feature_imports = []
    for feature_import in FeatureImport.objects.filter(
        created_at__lt=ten_minutes_ago,
        status=PROCESSING,
    ):
        feature_import.status = FAILED
        feature_imports.append(feature_import)
    FeatureImport.objects.bulk_update(feature_imports, ["status"])


def _export_features_for_environment(
    feature_export: FeatureExport, tag_ids: Optional[list[int]]
) -> None:
    """
    Caller for the export_features_for_environment to handle fails.
    """
    additional_filters = Q(
        identity__isnull=True,
        feature_segment__isnull=True,
        feature_state_value__isnull=False,
        feature__is_archived=False,
    )

    if tag_ids:
        additional_filters &= Q(feature__tags__in=tag_ids)

    environment = feature_export.environment
    feature_states = get_environment_flags_list(
        environment=environment,
        additional_filters=additional_filters,
    )

    payload = []
    for feature_state in feature_states:
        multivariate = [
            {
                "percentage_allocation": mv_fsv.percentage_allocation,
                "default_percentage_allocation": mv_fsv.multivariate_feature_option.default_percentage_allocation,
                "value": mv_fsv.multivariate_feature_option.value,
                "type": mv_fsv.multivariate_feature_option.type,
            }
            for mv_fsv in feature_state.multivariate_feature_state_values.select_related(
                "multivariate_feature_option"
            ).all()
        ]

        payload.append(
            {
                "name": feature_state.feature.name,
                "default_enabled": feature_state.feature.default_enabled,
                "is_server_key_only": feature_state.feature.is_server_key_only,
                "initial_value": feature_state.feature.initial_value,
                "value": feature_state.feature_state_value.value,
                "type": feature_state.feature_state_value.type,
                "enabled": feature_state.enabled,
                "multivariate": multivariate,
            }
        )

    feature_export.status = SUCCESS
    feature_export.data = json.dumps(payload)
    feature_export.save()


@register_task_handler()
def export_features_for_environment(
    feature_export_id: int, tag_ids: Optional[list[int]] = None
) -> None:
    feature_export = FeatureExport.objects.get(id=feature_export_id)
    try:
        _export_features_for_environment(feature_export, tag_ids)
        assert feature_export.status == SUCCESS
    except Exception:
        feature_export.status = FAILED
        feature_export.save()
        raise


@register_task_handler()
def import_features_for_environment(feature_import_id: int) -> None:
    feature_import = FeatureImport.objects.get(id=feature_import_id)
    try:
        _import_features_for_environment(feature_import)
        assert feature_import.status == SUCCESS
    except Exception:
        feature_import.status = FAILED
        feature_import.save()
        raise


def _import_features_for_environment(feature_import: FeatureImport) -> None:
    environment = feature_import.environment
    input_data = json.loads(feature_import.data)
    project = environment.project

    for feature_data in input_data:
        existing_feature = Feature.objects.filter(
            name=feature_data["name"],
            project=project,
        ).first()

        if existing_feature:
            # Leave existing features completely alone.
            if feature_import.strategy == SKIP:
                continue

            # First destroy existing features that overlap.
            if feature_import.strategy == OVERWRITE_DESTRUCTIVE:
                existing_feature.delete()

        _create_new_feature(feature_data, project, environment)

    feature_import.status = SUCCESS
    feature_import.save()


def _save_feature_state_value_with_type(
    value: Optional[Union[int, bool, str]],
    type: str,
    feature_state_value: FeatureStateValue,
) -> None:
    feature_state_value.type = type
    if feature_state_value.type == INTEGER:
        feature_state_value.integer_value = value
    elif feature_state_value.type == BOOLEAN:
        feature_state_value.boolean_value = value
    else:
        assert feature_state_value.type == STRING
        feature_state_value.string_value = value

    feature_state_value.save()


def _create_multivariate_feature_option(
    value: Optional[Union[int, bool, str]],
    type: str,
    feature: Feature,
    default_percentage_allocation: Union[int, float],
) -> MultivariateFeatureOption:
    mvfo = MultivariateFeatureOption(
        feature=feature,
        default_percentage_allocation=default_percentage_allocation,
        type=type,
    )
    if mvfo.type == INTEGER:
        mvfo.integer_value = value
    elif mvfo.type == BOOLEAN:
        mvfo.boolean_value = value
    else:
        assert mvfo.type == STRING
        mvfo.string_value = value

    mvfo.save()
    return mvfo


def _create_new_feature(
    feature_data: dict[str, Optional[Union[bool, str, int]]],
    project: Project,
    environment: Environment,
) -> None:
    feature = Feature.objects.create(
        name=feature_data["name"],
        project=project,
        initial_value=feature_data["initial_value"],
        is_server_key_only=feature_data["is_server_key_only"],
        default_enabled=feature_data["default_enabled"],
    )
    feature_state = feature.feature_states.get(
        environment=environment,
    )

    for mv_data in feature_data["multivariate"]:
        mv_feature_option = _create_multivariate_feature_option(
            value=mv_data["value"],
            type=mv_data["type"],
            feature=feature,
            default_percentage_allocation=mv_data["default_percentage_allocation"],
        )
        mv_feature_state_value = feature_state.multivariate_feature_state_values.filter(
            multivariate_feature_option=mv_feature_option
        ).first()
        mv_feature_state_value.percentage_allocation = mv_data["percentage_allocation"]
        mv_feature_state_value.save()

    feature_state_value = feature_state.feature_state_value
    _save_feature_state_value_with_type(
        value=feature_data["value"],
        type=feature_data["type"],
        feature_state_value=feature_state_value,
    )
    feature_state.enabled = feature_data["enabled"]
    feature_state.save()


# Should only run on official flagsmith instance.
if (
    settings.FLAGSMITH_ON_FLAGSMITH_FEATURE_EXPORT_ENVIRONMENT_ID
    and settings.FLAGSMITH_ON_FLAGSMITH_FEATURE_EXPORT_TAG_ID
):

    @register_recurring_task(
        run_every=timedelta(hours=24),
    )
    def create_flagsmith_on_flagsmith_feature_export_task():
        # Defined in a one off function for testing import.
        _create_flagsmith_on_flagsmith_feature_export()


def _create_flagsmith_on_flagsmith_feature_export():
    """
    This is called by create_flagsmith_on_flagsmith_feature_export_task
    and by tests. Should not be used by normal applications.
    """
    environment_id = settings.FLAGSMITH_ON_FLAGSMITH_FEATURE_EXPORT_ENVIRONMENT_ID
    tag_id = settings.FLAGSMITH_ON_FLAGSMITH_FEATURE_EXPORT_TAG_ID

    feature_export = FeatureExport.objects.create(
        environment_id=environment_id,
        status=PROCESSING,
    )

    export_features_for_environment(
        feature_export_id=feature_export.id,
        tag_ids=[tag_id],
    )

    feature_export.refresh_from_db()

    assert feature_export.status == SUCCESS

    FlagsmithOnFlagsmithFeatureExport.objects.create(feature_export=feature_export)
