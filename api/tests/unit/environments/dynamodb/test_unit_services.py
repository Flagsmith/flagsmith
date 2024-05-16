from decimal import Decimal

from mypy_boto3_dynamodb.service_resource import Table
from pytest_mock import MockerFixture

from environments.dynamodb import (
    DynamoEnvironmentV2Wrapper,
    DynamoIdentityWrapper,
)
from environments.dynamodb.services import migrate_environments_to_v2
from environments.dynamodb.wrappers.exceptions import CapacityBudgetExceeded
from environments.identities.models import Identity
from environments.models import Environment
from features.models import FeatureState
from projects.models import EdgeV2MigrationStatus
from util.mappers import (
    map_engine_feature_state_to_identity_override,
    map_engine_identity_to_identity_document,
    map_environment_to_environment_v2_document,
    map_identity_override_to_identity_override_document,
    map_identity_to_engine,
    map_identity_to_identity_document,
)


def test_migrate_environments_to_v2__environment_with_overrides__writes_expected(
    environment: Environment,
    identity: Identity,
    identity_featurestate: FeatureState,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    dynamodb_wrapper_v2: DynamoEnvironmentV2Wrapper,
    flagsmith_environments_v2_table: Table,
) -> None:
    # Given
    engine_identity = map_identity_to_engine(identity, with_overrides=True)
    dynamodb_identity_wrapper.put_item(
        map_engine_identity_to_identity_document(engine_identity)
    )

    expected_environment_document = map_environment_to_environment_v2_document(
        environment
    )
    expected_identity_override_document = (
        map_identity_override_to_identity_override_document(
            map_engine_feature_state_to_identity_override(
                feature_state=engine_identity.identity_features[0],
                identity_uuid=str(engine_identity.identity_uuid),
                identifier=engine_identity.identifier,
                environment_api_key=environment.api_key,
                environment_id=environment.id,
            ),
        )
    )

    # When
    migrate_environments_to_v2(
        project_id=environment.project_id,
        capacity_budget=float("Inf"),
    )

    # Then
    results = flagsmith_environments_v2_table.scan()["Items"]
    assert len(results) == 2
    assert results[0] == expected_environment_document
    assert results[1] == expected_identity_override_document


def test_migrate_environments_to_v2__wrapper_disabled__does_not_write(
    mocker: MockerFixture,
) -> None:
    # Given
    mocked_dynamodb_identity_wrapper = mocker.patch(
        "environments.dynamodb.services.DynamoIdentityWrapper",
        autospec=True,
        return_value=mocker.MagicMock(is_enabled=False),
    )
    mocked_dynamodb_v2_wrapper = mocker.patch(
        "environments.dynamodb.services.DynamoEnvironmentV2Wrapper",
        autospec=True,
        return_value=mocker.MagicMock(is_enabled=False),
    )

    # When
    migrate_environments_to_v2(
        project_id=mocker.Mock(),
        capacity_budget=mocker.Mock(),
    )

    # Then
    mocked_dynamodb_identity_wrapper.return_value.assert_not_called()
    mocked_dynamodb_v2_wrapper.return_value.assert_not_called()


def test_migrate_environments_to_v2__capacity_budget_exceeded__returns_expected(
    environment: Environment,
    identity: Identity,
    identity_featurestate: FeatureState,
    mocker: MockerFixture,
) -> None:
    # Given
    expected_capacity_budget = Decimal(12)
    mocked_dynamodb_identity_wrapper = mocker.MagicMock(spec=DynamoIdentityWrapper)

    def iter_all_items_paginated_gen_mock(**_):
        yield map_identity_to_identity_document(identity)
        raise CapacityBudgetExceeded(expected_capacity_budget, Decimal(13))

    mocked_dynamodb_identity_wrapper.iter_all_items_paginated.side_effect = (
        iter_all_items_paginated_gen_mock
    )
    mocker.patch(
        "environments.dynamodb.services.DynamoIdentityWrapper",
        autospec=True,
        return_value=mocked_dynamodb_identity_wrapper,
    )
    mocker.patch(
        "environments.dynamodb.services.DynamoEnvironmentV2Wrapper",
        autospec=True,
        return_value=mocker.MagicMock(),
    )

    # When
    result = migrate_environments_to_v2(
        project_id=environment.project_id,
        capacity_budget=expected_capacity_budget,
    )

    # Then
    mocked_dynamodb_identity_wrapper.iter_all_items_paginated.assert_called_once_with(
        environment_api_key=environment.api_key,
        capacity_budget=expected_capacity_budget,
        projection_expression="environment_api_key, identifier, identity_features, identity_uuid",
        overrides_only=True,
    )

    assert result.status == EdgeV2MigrationStatus.INCOMPLETE
    assert result.identity_overrides_changeset.to_put == []
