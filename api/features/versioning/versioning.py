import typing

from django.db.models import Q, QuerySet
from django.utils import timezone

from environments.models import Environment
from features.models import FeatureState


def get_environment_flags_queryset(
    environment_id: int, feature_name: str = None
) -> QuerySet[FeatureState]:
    """
    Get a queryset of the latest live versions of an environments' feature states
    """
    feature_states_list = get_environment_flags_list(environment_id, feature_name)
    return FeatureState.objects.filter(id__in=[fs.id for fs in feature_states_list])


def get_environment_flags_list(
    environment_id: int,
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
    environment = Environment.objects.get(id=environment_id)
    if environment.use_v2_feature_versioning:
        return _get_latest_environment_flags_v2(
            environment, feature_name, additional_filters
        )
    else:
        return _get_latest_environment_flags_v1(
            environment, feature_name, additional_filters
        )


def _get_latest_environment_flags_v2(
    environment: "Environment", feature_name: str = None, additional_filters: Q = None
) -> typing.List[FeatureState]:
    queryset = FeatureState.objects.filter(environment=environment)
    if additional_filters:
        queryset = queryset.filter(additional_filters)
    if feature_name:
        queryset = queryset.filter(feature__name=feature_name)

    queryset = queryset.select_related(
        "environment_feature_version", "feature", "environment"
    )

    feature_states_dict = {}
    for feature_state in queryset:
        key = (
            feature_state.feature_id,
            feature_state.feature_segment_id,
            feature_state.identity_id,
        )
        current_feature_state = feature_states_dict.get(key)
        if (
            not current_feature_state
            or feature_state.environment_feature_version
            > current_feature_state.environment_feature_version
        ):
            feature_states_dict[key] = feature_state

    return list(feature_states_dict.values())


def _get_latest_environment_flags_v1(
    environment: Environment, feature_name: str = None, additional_filters: Q = None
) -> typing.List[FeatureState]:
    # Get all feature states for a given environment with a valid live_from in the
    # past. Note: includes all versions for a given environment / feature
    # combination. We filter for the latest version later on.
    feature_states = FeatureState.objects.select_related(
        "feature", "feature_state_value"
    ).filter(
        environment_id=environment.id,
        live_from__isnull=False,
        live_from__lte=timezone.now(),
        version__isnull=False,
        deleted_at__isnull=True,
    )
    if feature_name:
        feature_states = feature_states.filter(feature__name__iexact=feature_name)

    if additional_filters:
        feature_states = feature_states.filter(additional_filters)

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
        # we use live_from here as a priority over the version since
        # the version is given when change requests are committed,
        # hence the version for a feature state that is scheduled
        # further in the future can be lower than a feature state
        # whose live_from value is earlier.
        # See: https://github.com/Flagsmith/flagsmith/issues/2030
        if not current_feature_state or feature_state.is_more_recent_live_from(
            current_feature_state
        ):
            feature_states_dict[key] = feature_state

    return list(feature_states_dict.values())
