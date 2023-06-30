import typing

from features.dataclasses import EnvironmentFeatureOverridesData
from features.versioning.versioning import get_environment_flags_list

if typing.TYPE_CHECKING:
    from environments.models import Environment


def get_overrides_data(
    environment: "Environment",
) -> typing.Dict[int, EnvironmentFeatureOverridesData]:
    """
    Get the number of identity / segment overrides in a given environment for each feature in the
    project.

    :param environment_id: the id of the environment to get the overrides data for
    :return: dictionary of {feature_id: EnvironmentFeatureOverridesData}
    """
    environment_feature_states_list = get_environment_flags_list(environment)
    all_overrides_data = {}

    for feature_state in environment_feature_states_list:
        env_feature_overrides_data = all_overrides_data.setdefault(
            feature_state.feature_id, EnvironmentFeatureOverridesData()
        )
        if feature_state.feature_segment_id:
            env_feature_overrides_data.num_segment_overrides += 1
        elif feature_state.identity_id:
            env_feature_overrides_data.add_identity_override()
        all_overrides_data[feature_state.feature_id] = env_feature_overrides_data

    return all_overrides_data  # noqa
