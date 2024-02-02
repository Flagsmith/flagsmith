from typing import TYPE_CHECKING
from unittest.mock import ANY

import pytest

from edge_api.identities.models import EdgeIdentity
from environments.identities.models import Identity
from features.features_service import (
    get_core_overrides_data,
    get_edge_overrides_data,
    get_overrides_data,
)
from features.models import Feature, FeatureSegment, FeatureState
from projects.models import IdentityOverridesV2MigrationStatus
from util.mappers.engine import (
    map_feature_state_to_engine,
    map_identity_to_engine,
)

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from environments.dynamodb import (
        DynamoEnvironmentV2Wrapper,
        DynamoIdentityWrapper,
    )
    from environments.models import Environment
    from segments.models import Segment


@pytest.fixture
def distinct_segment_featurestate(
    environment: "Environment",
    segment: "Segment",
) -> FeatureState:
    feature = Feature.objects.create(
        project=environment.project, name="distinct_feature_1"
    )
    feature_segment = FeatureSegment.objects.create(
        feature=feature, segment=segment, environment=environment
    )
    return FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment,
    )


@pytest.fixture
def distinct_identity_featurestate(
    environment: "Environment",
    identity: Identity,
) -> FeatureState:
    feature = Feature.objects.create(
        project=environment.project, name="distinct_feature_2"
    )
    return FeatureState.objects.create(
        feature=feature, environment=environment, identity=identity
    )


@pytest.mark.parametrize(
    "enable_dynamo_db, identity_overrides_v2_migration_status, expected_overrides_getter_name, expected_kwargs",
    [
        (
            True,
            IdentityOverridesV2MigrationStatus.NOT_STARTED,
            "get_core_overrides_data",
            {"skip_identity_overrides": True},
        ),
        (
            True,
            IdentityOverridesV2MigrationStatus.IN_PROGRESS,
            "get_core_overrides_data",
            {"skip_identity_overrides": True},
        ),
        (
            True,
            IdentityOverridesV2MigrationStatus.COMPLETE,
            "get_edge_overrides_data",
            {},
        ),
        (
            False,
            ANY,
            "get_core_overrides_data",
            {},
        ),
    ],
)
def test_feature_get_overrides_data__call_expected(
    mocker: "MockerFixture",
    environment: "Environment",
    enable_dynamo_db: bool,
    identity_overrides_v2_migration_status: str,
    expected_overrides_getter_name: str,
    expected_kwargs: dict[str, bool],
) -> None:
    # Given
    mocked_override_getters = {
        "get_core_overrides_data": mocker.patch(
            "features.features_service.get_core_overrides_data",
            autospec=True,
        ),
        "get_edge_overrides_data": mocker.patch(
            "features.features_service.get_edge_overrides_data",
            autospec=True,
        ),
    }
    environment.project.enable_dynamo_db = enable_dynamo_db
    environment.project.identity_overrides_v2_migration_status = (
        identity_overrides_v2_migration_status
    )

    # When
    get_overrides_data(environment)

    # Then
    mocked_override_getters.pop(expected_overrides_getter_name).assert_called_once_with(
        environment,
        **expected_kwargs,
    )
    [remaining_override_getter_mock] = mocked_override_getters.values()
    remaining_override_getter_mock.assert_not_called()


@pytest.mark.parametrize(
    "identity_overrides_v2_migration_status",
    [
        IdentityOverridesV2MigrationStatus.NOT_STARTED,
        IdentityOverridesV2MigrationStatus.IN_PROGRESS,
    ],
)
def test_feature_get_overrides_data__edge_project_not_migrated_to_v2__return_expected(
    environment: "Environment",
    distinct_identity_featurestate: FeatureState,
    distinct_segment_featurestate: FeatureState,
    identity_overrides_v2_migration_status: str,
) -> None:
    # Given
    environment.project.enable_dynamo_db = True
    environment.project.identity_overrides_v2_migration_status = (
        identity_overrides_v2_migration_status
    )

    # When
    overrides_data = get_overrides_data(environment)

    # Then
    assert (
        overrides_data[distinct_segment_featurestate.feature_id].num_segment_overrides
        == 1
    )
    assert (
        overrides_data[distinct_segment_featurestate.feature_id].num_identity_overrides
        is None
    )
    assert (
        overrides_data[distinct_identity_featurestate.feature_id].num_segment_overrides
        == 0
    )
    assert (
        overrides_data[distinct_identity_featurestate.feature_id].num_identity_overrides
        is None
    )


def test_feature_get_core_overrides_data(
    feature: Feature,
    environment: "Environment",
    identity: Identity,
    segment: "Segment",
    feature_segment: "FeatureSegment",
    identity_featurestate: FeatureState,
    segment_featurestate: FeatureState,
    distinct_segment_featurestate: FeatureState,
    distinct_identity_featurestate: FeatureState,
) -> None:
    # Given
    # and an override for another identity that has been deleted
    another_identity = Identity.objects.create(
        identifier="another-identity", environment=environment
    )
    fs_to_delete = FeatureState.objects.create(
        feature=feature, environment=environment, identity=another_identity
    )
    fs_to_delete.delete()

    # When
    overrides_data = get_core_overrides_data(environment)

    # Then
    assert overrides_data[feature.id].num_identity_overrides == 1
    assert overrides_data[feature.id].num_segment_overrides == 1

    assert (
        overrides_data[distinct_identity_featurestate.feature.id].num_identity_overrides
        == 1
    )
    assert (
        overrides_data[distinct_identity_featurestate.feature.id].num_segment_overrides
        == 0
    )

    assert (
        overrides_data[distinct_segment_featurestate.feature.id].num_identity_overrides
        is None
    )
    assert (
        overrides_data[distinct_segment_featurestate.feature.id].num_segment_overrides
        == 1
    )


@pytest.mark.django_db(transaction=True)
def test_feature_get_edge_overrides_data(
    feature: Feature,
    environment: "Environment",
    identity: Identity,
    segment: "Segment",
    feature_segment: "FeatureSegment",
    identity_featurestate: FeatureState,
    segment_featurestate: FeatureState,
    distinct_segment_featurestate: FeatureState,
    distinct_identity_featurestate: FeatureState,
    dynamodb_identity_wrapper: "DynamoIdentityWrapper",
    dynamodb_wrapper_v2: "DynamoEnvironmentV2Wrapper",
) -> None:
    # Given
    # replicate identity to Edge
    edge_identity = EdgeIdentity(map_identity_to_engine(identity, with_overrides=False))
    edge_identity.add_feature_override(
        map_feature_state_to_engine(identity_featurestate),
    )
    edge_identity.add_feature_override(
        map_feature_state_to_engine(distinct_identity_featurestate),
    )
    edge_identity.save()

    # When
    overrides_data = get_edge_overrides_data(environment)

    # Then
    assert overrides_data[feature.id].num_identity_overrides == 1
    assert overrides_data[feature.id].num_segment_overrides == 1

    assert (
        overrides_data[distinct_identity_featurestate.feature.id].num_identity_overrides
        == 1
    )
    assert (
        overrides_data[distinct_identity_featurestate.feature.id].num_segment_overrides
        == 0
    )

    assert (
        overrides_data[distinct_segment_featurestate.feature.id].num_identity_overrides
        is None
    )
    assert (
        overrides_data[distinct_segment_featurestate.feature.id].num_segment_overrides
        == 1
    )


@pytest.mark.django_db(transaction=True)
def test_get_edge_overrides_data_skips_deleted_features(
    feature: Feature,
    environment: "Environment",
    identity: Identity,
    identity_featurestate: FeatureState,
    distinct_identity_featurestate: FeatureState,
    dynamodb_identity_wrapper: "DynamoIdentityWrapper",
    dynamodb_wrapper_v2: "DynamoEnvironmentV2Wrapper",
):
    # Given
    # replicate identity to Edge
    edge_identity = EdgeIdentity(map_identity_to_engine(identity, with_overrides=False))
    # Create identity override for two different features
    edge_identity.add_feature_override(
        map_feature_state_to_engine(identity_featurestate),
    )
    edge_identity.add_feature_override(
        map_feature_state_to_engine(distinct_identity_featurestate),
    )
    edge_identity.save()

    # Now, delete one of the feature
    feature.delete()

    # When
    overrides_data = get_edge_overrides_data(environment)

    # Then - we only have one identity override(for the feature that still exists)
    assert len(overrides_data) == 1
    assert (
        overrides_data[distinct_identity_featurestate.feature.id].num_identity_overrides
        == 1
    )
