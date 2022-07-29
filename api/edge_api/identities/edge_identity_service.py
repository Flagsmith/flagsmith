import typing

from django.db.models import Prefetch, Q
from flag_engine.features.models import FeatureStateModel
from flag_engine.identities.models import IdentityModel

from environments.identities.models import Identity
from environments.models import Environment
from features.models import FeatureState
from features.multivariate.models import MultivariateFeatureStateValue


def get_all_feature_states_for_edge_identity(
    identity: IdentityModel,
) -> typing.Tuple[
    typing.List[typing.Union[FeatureState, FeatureStateModel]], typing.Set[str]
]:
    """
    Get all feature states for a flag engine identity model. The list returned by
    this function contains two distinct types: features.models.FeatureState &
    flag_engine.features.models.FeatureStateModel.

    :param identity: the IdentityModel to get the feature states for
    :return: tuple of (list of feature states, set of feature names that were overridden
        for the identity specifically)
    """
    segment_ids = Identity.dynamo_wrapper.get_segment_ids(identity)
    django_environment = Environment.objects.get(api_key=identity.environment_api_key)

    q = Q(identity__isnull=True) & (
        Q(feature_segment__segment__id__in=segment_ids)
        | Q(feature_segment__isnull=True)
    )
    environment_and_segment_feature_states = (
        django_environment.feature_states.select_related(
            "feature",
            "feature_segment",
            "feature_segment__segment",
            "feature_state_value",
        )
        .prefetch_related(
            Prefetch(
                "multivariate_feature_state_values",
                queryset=MultivariateFeatureStateValue.objects.select_related(
                    "multivariate_feature_option"
                ),
            )
        )
        .filter(q)
    )

    feature_states = {}
    for feature_state in environment_and_segment_feature_states:
        if (
            feature_state.feature.name not in feature_states
            or feature_state.feature_segment_id is not None
        ):
            feature_states[feature_state.feature.name] = feature_state

    identity_feature_states = identity.identity_features
    identity_feature_names = set()
    for identity_feature_state in identity_feature_states:
        feature_name = identity_feature_state.feature.name
        feature_states[feature_name] = identity_feature_state
        identity_feature_names.add(feature_name)

    return list(feature_states.values()), identity_feature_names
