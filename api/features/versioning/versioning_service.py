import typing

from django.db.models import Prefetch, Q, QuerySet
from django.utils import timezone

from features.models import FeatureState
from features.versioning.models import EnvironmentFeatureVersion

if typing.TYPE_CHECKING:
    from environments.models import Environment


def get_environment_flags_queryset(
    environment: "Environment", feature_name: str = None
) -> QuerySet[FeatureState]:
    """
    Get a queryset of the latest live versions of an environments' feature states
    """
    feature_states_list = get_environment_flags_list(environment, feature_name)
    return FeatureState.objects.filter(id__in=[fs.id for fs in feature_states_list])


def get_environment_flags_list(
    environment: "Environment",
    feature_name: str = None,
    additional_filters: Q = None,
    additional_select_related_args: typing.Iterable[str] = None,
    additional_prefetch_related_args: typing.Iterable[
        typing.Union[str, Prefetch]
    ] = None,
) -> typing.List["FeatureState"]:
    """
    Get a list of the latest committed versions of FeatureState objects that are
    associated with the given environment. Can be filtered to remove segment /
    identity overrides using additional_filters argument.

    Note: uses a single query to get all valid versions of a given environment's
    feature states. The logic to grab the latest version is then handled in python
    by building a dictionary. Returns a list of FeatureState objects.
    """
    additional_select_related_args = additional_select_related_args or tuple()
    additional_prefetch_related_args = additional_prefetch_related_args or tuple()

    feature_states = (
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
        feature_states = feature_states.filter(feature__name__iexact=feature_name)

    # Build up a dictionary in the form
    # {(feature_id, feature_segment_id, identity_id): feature_state}
    # and only keep the latest version for each feature.
    feature_states_dict = {}
    for feature_state in feature_states:
        key = (
            feature_state.feature_id,
            getattr(feature_state.feature_segment, "segment_id", None),
            feature_state.identity_id,
        )
        current_feature_state = feature_states_dict.get(key)
        if not current_feature_state or feature_state > current_feature_state:
            feature_states_dict[key] = feature_state

    return list(feature_states_dict.values())


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
