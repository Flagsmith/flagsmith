import typing
from concurrent.futures import ThreadPoolExecutor

from edge_api.identities.edge_identity_service import (
    get_edge_identity_overrides,
)
from features.dataclasses import EnvironmentFeatureOverridesData
from features.versioning.versioning_service import get_environment_flags_list
from projects.models import IdentityOverridesV2MigrationStatus

if typing.TYPE_CHECKING:
    from environments.models import Environment


OverridesData = dict[int, EnvironmentFeatureOverridesData]


def get_overrides_data(
    environment: "Environment",
) -> OverridesData:
    """
    Get correct overrides counts for a given environment.

    :param project: project to get overrides data for
    :return: overrides data getter
    """
    project = environment.project
    match project.enable_dynamo_db, project.identity_overrides_v2_migration_status:
        case True, IdentityOverridesV2MigrationStatus.COMPLETE:
            # If v2 migration is complete, count segment overrides from Core
            # and identity overrides from DynamoDB.
            return get_edge_overrides_data(environment)
        case True, _:
            # If v2 migration is in progress or not started, we want to count Core overrides,
            # but only the segment ones, as the identity ones in DynamoDB are uncountable for v1.
            return get_core_overrides_data(
                environment,
                skip_identity_overrides=True,
            )
        case _, _:
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
            env_feature_overrides_data.add_identity_override()

    return all_overrides_data


def get_edge_overrides_data(
    environment: "Environment",
) -> OverridesData:
    """
    Get the number of identity / segment overrides in a given environment for each feature in the
    project.
    Retrieve identity override data from DynamoDB.

    :param environment: the environment to get the overrides data for
    :return OverridesData: dictionary of {feature_id: EnvironmentFeatureOverridesData}
    """
    with ThreadPoolExecutor() as executor:
        get_environment_flags_list_future = executor.submit(
            get_environment_flags_list,
            environment,
        )
        get_overrides_data_future = executor.submit(
            get_edge_identity_overrides,
            environment_id=environment.id,
        )
    all_overrides_data: OverridesData = {}

    for feature_state in get_environment_flags_list_future.result():
        env_feature_overrides_data = all_overrides_data.setdefault(
            feature_state.feature_id, EnvironmentFeatureOverridesData()
        )
        if feature_state.feature_segment_id:
            env_feature_overrides_data.num_segment_overrides += 1
    for identity_override in get_overrides_data_future.result():
        # Only override features that exists in core
        if identity_override.feature_state.feature.id in all_overrides_data:
            all_overrides_data[
                identity_override.feature_state.feature.id
            ].add_identity_override()

    return all_overrides_data
