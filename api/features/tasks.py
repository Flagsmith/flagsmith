import json
from datetime import timedelta
from threading import Thread
from typing import Optional, Union

from django.db.models import Q
from django.utils import timezone

from environments.models import Environment, Webhook
from features.models import (
    Feature,
    FeatureExport,
    FeatureImport,
    FeatureState,
    FeatureStateValue,
)
from features.multivariate.models import MultivariateFeatureOption
from features.value_types import BOOLEAN, INTEGER, STRING
from features.versioning.versioning_service import get_environment_flags_list
from projects.models import Project
from task_processor.decorators import (
    register_recurring_task,
    register_task_handler,
)
from webhooks.constants import WEBHOOK_DATETIME_FORMAT
from webhooks.webhooks import (
    WebhookEventType,
    call_environment_webhooks,
    call_organisation_webhooks,
)

from .constants import OVERWRITE, SKIP
from .models import HistoricalFeatureState


@register_recurring_task(
    run_every=timedelta(hours=12),
)
def clear_stale_feature_imports_and_exports() -> None:
    two_weeks_ago = timezone.now() - timedelta(days=14)
    FeatureExport.objects.filter(created_date__lt=two_weeks_ago).delete()
    FeatureImport.objects.filter(created_date__lt=two_weeks_ago).delete()


@register_task_handler()
def export_features_for_environment(
    environment_id: int, tag_ids: Optional[list[int]] = None
) -> None:
    additional_filters = Q(
        identity__isnull=True,
        feature_segment__isnull=True,
        feature_state_value__isnull=False,
        feature__is_archived=False,
    )

    if tag_ids:
        additional_filters &= Q(feature__tags__in=tag_ids)

    environment = Environment.objects.get(id=environment_id)
    feature_states = get_environment_flags_list(
        environment=environment,
        additional_filters=additional_filters,
    )

    payload = []
    for feature_state in feature_states:
        multivariate = []
        for mv_option in feature_state.feature.multivariate_options.all():
            mv_feature_state_value = (
                feature_state.multivariate_feature_state_values.filter(
                    multivariate_feature_option=mv_option
                ).first()
            )

            multivariate.append(
                {
                    "percentage_allocation": mv_feature_state_value.percentage_allocation,
                    "default_percentage_allocation": mv_option.default_percentage_allocation,
                    "value": mv_option.value,
                }
            )

        payload.append(
            {
                "name": feature_state.feature.name,
                "default_enabled": feature_state.feature.default_enabled,
                "is_server_key_only": feature_state.feature.is_server_key_only,
                "initial_value": feature_state.feature.initial_value,
                "value": feature_state.feature_state_value.value,
                "enabled": feature_state.enabled,
                "multivariate": multivariate,
            }
        )

    FeatureExport.objects.create(
        environment_id=environment_id, data=json.dumps(payload)
    )


@register_task_handler()
def import_features_for_environment(feature_import_id: int) -> None:
    feature_import = FeatureImport.objects.get(id=feature_import_id)
    environment = feature_import.environment
    input_data = json.loads(feature_import.data)
    project = environment.project

    for rec in input_data:
        existing_feature = Feature.objects.filter(
            name=rec["name"],
            project=project,
        ).first()

        if existing_feature:
            # Leave existing features completely alone.
            if feature_import.strategy == SKIP:
                continue

            # First destroy existing features that overlap.
            if feature_import.strategy == OVERWRITE:
                existing_feature.delete()

        _create_new_feature(rec, project, environment)


def trigger_feature_state_change_webhooks(
    instance: FeatureState, event_type: WebhookEventType = WebhookEventType.FLAG_UPDATED
):
    assert event_type in [WebhookEventType.FLAG_UPDATED, WebhookEventType.FLAG_DELETED]

    history_instance = instance.history.first()
    timestamp = (
        history_instance.history_date.strftime(WEBHOOK_DATETIME_FORMAT)
        if history_instance and history_instance.history_date
        else ""
    )
    changed_by = (
        str(history_instance.history_user)
        if history_instance and history_instance.history_user
        else ""
    )

    new_state = (
        None
        if event_type == WebhookEventType.FLAG_DELETED
        else _get_feature_state_webhook_data(instance)
    )
    data = {"new_state": new_state, "changed_by": changed_by, "timestamp": timestamp}
    previous_state = _get_previous_state(history_instance, event_type)
    if previous_state:
        data.update(previous_state=previous_state)
    Thread(
        target=call_environment_webhooks,
        args=(instance.environment, data, event_type),
    ).start()

    Thread(
        target=call_organisation_webhooks,
        args=(
            instance.environment.project.organisation,
            data,
            event_type,
        ),
    ).start()


def _get_previous_state(
    history_instance: HistoricalFeatureState, event_type: WebhookEventType
) -> dict:
    if event_type == WebhookEventType.FLAG_DELETED:
        return _get_feature_state_webhook_data(history_instance.instance)
    if history_instance and history_instance.prev_record:
        return _get_feature_state_webhook_data(
            history_instance.prev_record.instance, previous=True
        )
    return None


def _get_feature_state_webhook_data(feature_state, previous=False):
    # TODO: fix circular imports and use serializers instead.
    feature_state_value = (
        feature_state.get_feature_state_value()
        if not previous
        else feature_state.previous_feature_state_value
    )

    return Webhook.generate_webhook_feature_state_data(
        feature_state.feature,
        environment=feature_state.environment,
        enabled=feature_state.enabled,
        value=feature_state_value,
        identity_id=feature_state.identity_id,
        identity_identifier=getattr(feature_state.identity, "identifier", None),
        feature_segment=feature_state.feature_segment,
    )


def _save_feature_state_value_with_type(
    value: Optional[Union[int, bool, str]], feature_state_value: FeatureStateValue
) -> None:
    if isinstance(value, int):
        feature_state_value.type = INTEGER
        feature_state_value.integer_value = value
    elif isinstance(value, bool):
        feature_state_value.type = BOOLEAN
        feature_state_value.boolean_value = value
    else:
        feature_state_value.type = STRING
        feature_state_value.string_value = value

    feature_state_value.save()


def _create_multivariate_feature_option(
    value: Optional[Union[int, bool, str]],
    feature: Feature,
    default_percentage_allocation: Union[int, float],
) -> MultivariateFeatureOption:
    if isinstance(value, int):
        mvfo = MultivariateFeatureOption.objects.create(
            integer_value=value,
            type=INTEGER,
            feature=feature,
            default_percentage_allocation=default_percentage_allocation,
        )
    elif isinstance(value, bool):
        mvfo = MultivariateFeatureOption.objects.create(
            boolean_value=value,
            type=BOOLEAN,
            feature=feature,
            default_percentage_allocation=default_percentage_allocation,
        )
    else:
        mvfo = MultivariateFeatureOption.objects.create(
            string_value=value,
            type=STRING,
            feature=feature,
            default_percentage_allocation=default_percentage_allocation,
        )
    return mvfo


def _create_new_feature(
    rec: dict[str, Optional[Union[bool, str, int]]],
    project: Project,
    environment: Environment,
) -> None:
    feature = Feature.objects.create(
        name=rec["name"],
        project=project,
        initial_value=rec["initial_value"],
        is_server_key_only=rec["is_server_key_only"],
        default_enabled=rec["default_enabled"],
    )
    feature_state = feature.feature_states.filter(
        environment=environment,
    ).first()

    for mv_rec in rec["multivariate"]:
        mv_feature_option = _create_multivariate_feature_option(
            mv_rec["value"],
            feature,
            mv_rec["default_percentage_allocation"],
        )
        mv_feature_state_value = feature_state.multivariate_feature_state_values.filter(
            multivariate_feature_option=mv_feature_option
        ).first()
        mv_feature_state_value.percentage_allocation = mv_rec["percentage_allocation"]
        mv_feature_state_value.save()

    feature_state_value = feature_state.feature_state_value
    _save_feature_state_value_with_type(rec["value"], feature_state_value)
    feature_state.enabled = rec["enabled"]
    feature_state.save()
