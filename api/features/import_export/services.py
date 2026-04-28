from django.db.models import Q

from environments.models import Environment
from features.import_export.types import FeatureExportData
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import MultivariateFeatureOption


def overwrite_feature_for_environment(
    feature_data: FeatureExportData,
    existing_feature: Feature,
    environment: Environment,
) -> None:
    """
    Apply a destructive feature import to a single environment without
    affecting other environments' feature states or the Feature definition.
    """
    FeatureSegment.objects.filter(
        feature=existing_feature, environment=environment
    ).delete()
    existing_feature.feature_states.filter(
        environment=environment, identity__isnull=False
    ).delete()

    feature_state = FeatureState.objects.get_live_feature_states(
        environment=environment,
        additional_filters=Q(
            feature=existing_feature,
            identity__isnull=True,
            feature_segment__isnull=True,
        ),
    ).get()

    existing_options_by_value: dict[
        tuple[str | None, str | int | bool | None], MultivariateFeatureOption
    ] = {
        (option.type, option.value): option
        for option in existing_feature.multivariate_options.all()
    }
    imported_option_ids: set[int] = set()
    for mv_data in feature_data["multivariate"]:
        key = (mv_data["type"], mv_data["value"])
        mv_option = existing_options_by_value.get(key)
        if mv_option is None:
            mv_option = MultivariateFeatureOption(
                feature=existing_feature,
                default_percentage_allocation=mv_data["default_percentage_allocation"],
                type=mv_data["type"],
            )
            setattr(
                mv_option,
                FeatureState.get_feature_state_key_name(mv_data["type"]),
                mv_data["value"],
            )
            mv_option.save()
        imported_option_ids.add(mv_option.pk)
        mv_state_value = feature_state.multivariate_feature_state_values.get(
            multivariate_feature_option=mv_option,
        )
        mv_state_value.percentage_allocation = mv_data["percentage_allocation"]
        mv_state_value.save()

    for mv_state_value in feature_state.multivariate_feature_state_values.exclude(
        multivariate_feature_option_id__in=imported_option_ids,
    ):
        if mv_state_value.percentage_allocation != 0:
            mv_state_value.percentage_allocation = 0
            mv_state_value.save()

    feature_state_value = feature_state.feature_state_value
    feature_state_value.type = feature_data["type"]
    setattr(
        feature_state_value,
        FeatureState.get_feature_state_key_name(feature_data["type"]),
        feature_data["value"],
    )
    feature_state_value.save()
    feature_state.enabled = feature_data["enabled"]
    feature_state.save()
