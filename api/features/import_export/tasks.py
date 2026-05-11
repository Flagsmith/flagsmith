import json
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from task_processor.decorators import (
    register_recurring_task,
    register_task_handler,
)

from features.import_export.constants import (
    FAILED,
    PROCESSING,
    SKIP,
    SUCCESS,
)
from features.import_export.mappers import map_feature_export_data_to_feature
from features.import_export.models import (
    FeatureExport,
    FeatureImport,
    FlagsmithOnFlagsmithFeatureExport,
)
from features.import_export.services import overwrite_feature_for_environment
from features.import_export.types import FeatureExportData
from features.models import Feature
from features.versioning.versioning_service import get_environment_flags_list


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
    input_data: list[FeatureExportData] = json.loads(feature_import.data)
    project = environment.project

    for feature_data in input_data:
        existing_feature = Feature.objects.filter(
            name=feature_data["name"],
            project=project,
        ).first()

        if existing_feature and feature_import.strategy == SKIP:
            continue

        if existing_feature is None:
            existing_feature = map_feature_export_data_to_feature(feature_data, project)
            existing_feature.save()

        overwrite_feature_for_environment(feature_data, existing_feature, environment)

    feature_import.status = SUCCESS
    feature_import.save()


# Should only run on official flagsmith instance.
if (
    settings.FLAGSMITH_ON_FLAGSMITH_FEATURE_EXPORT_ENVIRONMENT_ID
    and settings.FLAGSMITH_ON_FLAGSMITH_FEATURE_EXPORT_TAG_ID
):

    @register_recurring_task(
        run_every=timedelta(hours=24),
    )
    def create_flagsmith_on_flagsmith_feature_export_task():  # type: ignore[no-untyped-def]
        # Defined in a one off function for testing import.
        _create_flagsmith_on_flagsmith_feature_export()  # type: ignore[no-untyped-call]


def _create_flagsmith_on_flagsmith_feature_export():  # type: ignore[no-untyped-def]
    """
    This is called by create_flagsmith_on_flagsmith_feature_export_task
    and by tests. Should not be used by normal applications.
    """
    environment_id = settings.FLAGSMITH_ON_FLAGSMITH_FEATURE_EXPORT_ENVIRONMENT_ID
    tag_id = settings.FLAGSMITH_ON_FLAGSMITH_FEATURE_EXPORT_TAG_ID

    feature_export = FeatureExport.objects.create(  # type: ignore[misc]
        environment_id=environment_id,
        status=PROCESSING,
    )

    export_features_for_environment(
        feature_export_id=feature_export.id,
        tag_ids=[tag_id],  # type: ignore[list-item]
    )

    feature_export.refresh_from_db()

    assert feature_export.status == SUCCESS

    FlagsmithOnFlagsmithFeatureExport.objects.create(feature_export=feature_export)
