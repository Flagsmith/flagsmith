import typing

from django.db.models import Q, QuerySet
from django.utils import timezone

from environments.models import Environment
from features.models import FeatureState


def get_environment_flags_queryset(
    environment: Environment, feature_name: str = None
) -> QuerySet[FeatureState]:
    """
    Get a queryset of the latest live versions of an environments' feature states
    """
    feature_states_list = get_environment_flags_list(environment, feature_name)
    return FeatureState.objects.filter(id__in=[fs.id for fs in feature_states_list])


def get_environment_flags_list(
    environment: Environment,
    feature_name: str = None,
    additional_filters: Q = None,
) -> typing.List["FeatureState"]:
    """
    Get a list of the latest committed versions of FeatureState objects that are
    associated with the given environment. Can be filtered to remove segment /
    identity overrides using additional_filters argument.

    Note: uses a single query to get all valid versions of a given environment's
    feature states. The logic to grab the latest version is then handled in python
    by building a dictionary. Returns a list of FeatureState objects.
    """
    qs_filter = _build_environment_flags_qs_filter(
        environment, feature_name, additional_filters
    )

    feature_states = FeatureState.objects.select_related(
        "feature", "feature_state_value", "environment_feature_version"
    ).filter(qs_filter)

    # Build up a dictionary in the form
    # {(feature_id, feature_segment_id, identity_id): feature_state}
    # and only keep the latest version for each feature.
    feature_states_dict = {}
    for feature_state in feature_states:
        key = (
            feature_state.feature_id,
            feature_state.feature_segment_id,
            feature_state.identity_id,
        )
        current_feature_state = feature_states_dict.get(key)
        if not current_feature_state or feature_state > current_feature_state:
            feature_states_dict[key] = feature_state

    return list(feature_states_dict.values())


def _build_environment_flags_qs_filter(
    environment: Environment, feature_name: str = None, additional_filters: Q = None
) -> Q:
    qs_filter = Q(environment=environment, deleted_at__isnull=True)
    if not environment.use_v2_feature_versioning:
        qs_filter &= Q(
            live_from__isnull=False,
            live_from__lte=timezone.now(),
            version__isnull=False,
        )

    if feature_name:
        qs_filter &= Q(feature__name__iexact=feature_name)
    if additional_filters:
        qs_filter &= additional_filters

    return qs_filter
