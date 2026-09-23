import typing
from concurrent.futures import ThreadPoolExecutor

from django.db.models import Q

from edge_api.identities.edge_identity_service import (
    get_edge_identity_override_keys,
)
from environments.dynamodb.utils import (
    get_feature_id_from_identity_override_document_key,
)
from features.dataclasses import EnvironmentFeatureOverridesData
from features.versioning.versioning_service import get_environment_flags_list

if typing.TYPE_CHECKING:
    from environments.models import Environment


OverridesData = dict[int, EnvironmentFeatureOverridesData]


def get_overrides_data(
    environment: "Environment",
    *,
    feature_ids: typing.Collection[int],
) -> OverridesData:
    """
    Get correct overrides counts for the given features in a given environment.

    :param environment: environment to get overrides data for
    :param feature_ids: features to get overrides data for
    :return: overrides data getter dictionary of {feature_id: EnvironmentFeatureOverridesData}
    """
    project = environment.project

    if project.enable_dynamo_db:
        if project.edge_v2_identity_overrides_migrated:
            # If v2 migration is complete, count segment overrides from Core
            # and identity overrides from DynamoDB.
            return get_edge_overrides_data(environment, feature_ids=feature_ids)
        # If v2 migration is not started, in progress, or incomplete,
        # only count segment overrides from Core.
        # v1 Edge identity overrides are uncountable.
        return get_core_overrides_data(
            environment,
            feature_ids=feature_ids,
            skip_identity_overrides=True,
        )
    # For projects still fully on Core, count all overrides from Core.
    return get_core_overrides_data(environment, feature_ids=feature_ids)


def get_core_overrides_data(
    environment: "Environment",
    *,
    feature_ids: typing.Collection[int],
    skip_identity_overrides: bool = False,
) -> OverridesData:
    """
    Get the number of identity / segment overrides in a given environment for each of the
    given features.

    :param environment: the environment to get the overrides data for
    :param feature_ids: features to get overrides data for
    :return OverridesData: dictionary of {feature_id: EnvironmentFeatureOverridesData}
    """
    environment_feature_states_list = get_environment_flags_list(
        environment,
        additional_filters=Q(feature_id__in=feature_ids),
    )
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
    environment: "Environment",
    *,
    feature_ids: typing.Collection[int],
) -> OverridesData:
    """
    Get the number of identity / segment overrides in a given environment for each of the
    given features.
    Retrieve identity override data from DynamoDB.

    :param environment: the environment to get the overrides data for
    :param feature_ids: features to get overrides data for
    :return OverridesData: dictionary of {feature_id: EnvironmentFeatureOverridesData}
    """

    with ThreadPoolExecutor() as executor:
        # Note: We intentionally let the get_environment_flags_list
        # call happen on the main thread to simplify testing.
        # The call to dynamo happens on a separate thread, which
        # still gives us the parallelism we need without needing
        # an extra thread. This does mean that the order of execution
        # is important here.
        get_overrides_data_future = executor.submit(
            get_edge_identity_override_keys,
            environment_id=environment.id,
        )
        flags_list = get_environment_flags_list(
            environment,
            additional_filters=Q(feature_id__in=feature_ids),
        )
    all_overrides_data: OverridesData = {}

    for feature_state in flags_list:
        env_feature_overrides_data = all_overrides_data.setdefault(
            feature_state.feature_id, EnvironmentFeatureOverridesData()
        )
        if feature_state.feature_segment_id:
            env_feature_overrides_data.num_segment_overrides += 1
    for identity_override_key in get_overrides_data_future.result():
        feature_id = get_feature_id_from_identity_override_document_key(
            identity_override_key
        )
        # Only override features that exists in core
        if feature_id in all_overrides_data:
            all_overrides_data[feature_id].add_identity_override()  # type: ignore[no-untyped-call]

    return all_overrides_data
