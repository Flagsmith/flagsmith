import typing

from django.db.models import Prefetch, Q, QuerySet
from django.utils import timezone

from environments.models import Environment
from features.models import FeatureState
from features.versioning.models import EnvironmentFeatureVersion


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
    additional_select_related_args: typing.Iterable[str] = None,
    additional_prefetch_related_args: typing.Iterable[
        typing.Union[str, Prefetch]
    ] = None,
) -> list[FeatureState]:
    """
    Get a list of the latest committed versions of FeatureState objects that are
    associated with the given environment. Can be filtered to remove segment /
    identity overrides using additional_filters argument.

    Note: uses a single query to get all valid versions of a given environment's
    feature states. The logic to grab the latest version is then handled in python
    by building a dictionary. Returns a list of FeatureState objects.
    """
    return list(
        get_environment_flags_dict(
            environment,
            feature_name,
            additional_filters,
            additional_select_related_args,
            additional_prefetch_related_args,
        ).values()
    )


def get_environment_flags_dict(
    environment: Environment,
    feature_name: str = None,
    additional_filters: Q = None,
    additional_select_related_args: typing.Iterable[str] = None,
    additional_prefetch_related_args: typing.Iterable[
        typing.Union[str, Prefetch]
    ] = None,
    key_function: typing.Callable[[FeatureState], tuple] = None,
) -> dict[tuple | str | int, FeatureState]:
    key_function = key_function or _get_distinct_key

    feature_states = _get_feature_states_queryset(
        environment,
        feature_name,
        additional_filters,
        additional_select_related_args,
        additional_prefetch_related_args,
    )

    # Build up a dictionary keyed off the relevant unique attributes as defined
    # by the provided key function and only keep the highest priority feature state
    # for each feature.
    feature_states_dict = {}
    for feature_state in feature_states:
        key = key_function(feature_state)
        current_feature_state = feature_states_dict.get(key)
        if not current_feature_state or feature_state > current_feature_state:
            feature_states_dict[key] = feature_state

    return feature_states_dict


def get_current_live_environment_feature_version(
    environment_id: int, feature_id: int
) -> EnvironmentFeatureVersion | None:
    return (
        EnvironmentFeatureVersion.objects.filter(
            environment_id=environment_id,
            feature_id=feature_id,
            published_at__isnull=False,
            live_from__lte=timezone.now(),
        )
        .order_by("-live_from")
        .first()
    )


def _get_feature_states_queryset(
    environment: "Environment",
    feature_name: str = None,
    additional_filters: Q = None,
    additional_select_related_args: typing.Iterable[str] = None,
    additional_prefetch_related_args: typing.Iterable[
        typing.Union[str, Prefetch]
    ] = None,
) -> QuerySet[FeatureState]:
    additional_select_related_args = additional_select_related_args or tuple()
    additional_prefetch_related_args = additional_prefetch_related_args or tuple()

    queryset = (
        FeatureState.objects.get_live_feature_states(
            environment=environment, additional_filters=additional_filters
        )
        .select_related(
            "environment",
            "feature",
            "feature_state_value",
            "environment_feature_version",
            "feature_segment",
            *additional_select_related_args,
        )
        .prefetch_related(*additional_prefetch_related_args)
    )

    if feature_name:
        queryset = queryset.filter(feature__name__iexact=feature_name)

    return queryset


def _get_distinct_key(
    feature_state: FeatureState,
) -> tuple[int, int | None, int | None]:
    return (
        feature_state.feature_id,
        getattr(feature_state.feature_segment, "segment_id", None),
        feature_state.identity_id,
    )
