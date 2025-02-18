import typing
from concurrent.futures import ThreadPoolExecutor

from edge_api.identities.edge_identity_service import (
    get_edge_identity_overrides_for_feature_ids,
)
from features.dataclasses import EnvironmentFeatureOverridesData
from features.versioning.versioning_service import get_environment_flags_list

if typing.TYPE_CHECKING:
    from environments.models import Environment


OverridesData = dict[int, EnvironmentFeatureOverridesData]


def get_overrides_data(
    environment: "Environment",
    feature_ids: None | list[int] = None,
) -> OverridesData:
    """
    Get correct overrides counts for a given environment.

    :param project: project to get overrides data for
    :return: overrides data getter dictionary of {feature_id: EnvironmentFeatureOverridesData}
    """
    project = environment.project

    if project.enable_dynamo_db:
        if project.edge_v2_identity_overrides_migrated:
            # If v2 migration is complete, count segment overrides from Core
            # and identity overrides from DynamoDB.
            return get_edge_overrides_data(environment, feature_ids)
        # If v2 migration is not started, in progress, or incomplete,
        # only count segment overrides from Core.
        # v1 Edge identity overrides are uncountable.
        return get_core_overrides_data(
            environment,
            skip_identity_overrides=True,
        )
    # For projects still fully on Core, count all overrides from Core.
    return get_core_overrides_data(environment)


def get_core_overrides_data(
    environment: "Environment",
    *,
    skip_identity_overrides: bool = False,
) -> OverridesData:
    """
    Get the number of identity / segment overrides in a given environment for each feature in the
    project.

    :param environment: the environment to get the overrides data for
    :return OverridesData: dictionary of {feature_id: EnvironmentFeatureOverridesData}
    """
    environment_feature_states_list = get_environment_flags_list(environment)
    all_overrides_data: OverridesData = {}

    for feature_state in environment_feature_states_list:
        env_feature_overrides_data = all_overrides_data.setdefault(
            feature_state.feature_id, EnvironmentFeatureOverridesData()
        )
        if feature_state.feature_segment_id:
            env_feature_overrides_data.num_segment_overrides += 1
        elif skip_identity_overrides:
            continue
        elif feature_state.identity_id:
            env_feature_overrides_data.add_identity_override()  # type: ignore[no-untyped-call]

    return all_overrides_data


def get_edge_overrides_data(
    environment: "Environment", feature_ids: None | list[int] = None
) -> OverridesData:
    """
    Get the number of identity / segment overrides in a given environment for each feature in the
    project.
    Retrieve identity override data from DynamoDB.

    :param environment: the environment to get the overrides data for
    :return OverridesData: dictionary of {feature_id: EnvironmentFeatureOverridesData}
    """

    assert feature_ids is not None

    with ThreadPoolExecutor() as executor:
        get_environment_flags_list_future = executor.submit(
            get_environment_flags_list,
            environment,
        )
        get_overrides_data_future = executor.submit(
            get_edge_identity_overrides_for_feature_ids,
            environment_id=environment.id,
            feature_ids=feature_ids,
        )
    all_overrides_data: OverridesData = {}

    for feature_state in get_environment_flags_list_future.result():
        env_feature_overrides_data = all_overrides_data.setdefault(
            feature_state.feature_id, EnvironmentFeatureOverridesData()
        )
        if feature_state.feature_segment_id:
            env_feature_overrides_data.num_segment_overrides += 1
    for identity_overrides_v2_list in get_overrides_data_future.result():

        for identity_override in identity_overrides_v2_list.identity_overrides:
            # Only override features that exists in core
            if identity_override.feature_state.feature.id in all_overrides_data:
                all_overrides_data[  # type: ignore[no-untyped-call]
                    identity_override.feature_state.feature.id
                ].add_identity_override()
                all_overrides_data[
                    identity_override.feature_state.feature.id
                ].is_num_identity_overrides_complete = (
                    identity_overrides_v2_list.is_num_identity_overrides_complete
                )

    return all_overrides_data
