import uuid

from mypy_boto3_dynamodb.service_resource import Table
from pytest_django.fixtures import SettingsWrapper

from environments.dynamodb.dynamodb_wrapper import DynamoEnvironmentV2Wrapper
from environments.dynamodb.types import (
    IdentityOverridesV2Changeset,
    IdentityOverrideV2,
)
from environments.models import Environment
from features.models import Feature, FeatureState
from util.mappers import (
    map_environment_to_environment_v2_document,
    map_feature_state_to_engine,
    map_identity_override_to_identity_override_document,
)


def test_environment_v2_wrapper__get_identity_overrides__return_expected(
    settings: SettingsWrapper,
    environment: Environment,
    flagsmith_environments_v2_table: Table,
    feature: Feature,
) -> None:
    # Given
    settings.ENVIRONMENTS_V2_TABLE_NAME_DYNAMO = flagsmith_environments_v2_table.name
    wrapper = DynamoEnvironmentV2Wrapper()

    identity_uuid = str(uuid.uuid4())
    identifier = "identity1"
    override_document = {
        "environment_id": str(environment.id),
        "document_key": f"identity_override:{feature.id}:{identity_uuid}",
        "environment_api_key": environment.api_key,
        "identifier": identifier,
        "feature_state": {},
    }

    environment_document = map_environment_to_environment_v2_document(environment)

    flagsmith_environments_v2_table.put_item(Item=override_document)
    flagsmith_environments_v2_table.put_item(Item=environment_document)

    # When
    results = wrapper.get_identity_overrides_by_feature_id(
        environment_id=environment.id,
        feature_id=feature.id,
    )

    # Then
    assert len(results) == 1
    assert results[0] == override_document


def test_environment_v2_wrapper__update_identity_overrides__put_expected(
    settings: SettingsWrapper,
    environment: Environment,
    flagsmith_environments_v2_table: Table,
    feature: Feature,
    feature_state: FeatureState,
) -> None:
    # Given
    settings.ENVIRONMENTS_V2_TABLE_NAME_DYNAMO = flagsmith_environments_v2_table.name
    wrapper = DynamoEnvironmentV2Wrapper()

    identity_uuid = str(uuid.uuid4())
    identifier = "identity1"
    override_document = IdentityOverrideV2.parse_obj(
        {
            "environment_id": str(environment.id),
            "document_key": f"identity_override:{feature.id}:{identity_uuid}",
            "environment_api_key": environment.api_key,
            "feature_state": map_feature_state_to_engine(feature_state),
            "identifier": identifier,
            "identity_uuid": identity_uuid,
        }
    )

    # When
    wrapper.update_identity_overrides(
        changeset=IdentityOverridesV2Changeset(
            to_delete=[],
            to_put=[override_document],
        ),
    )

    # Then
    results = flagsmith_environments_v2_table.scan()["Items"]
    assert len(results) == 1
    assert results[0] == map_identity_override_to_identity_override_document(
        override_document,
    )


def test_environment_v2_wrapper__update_identity_overrides__delete_expected(
    settings: SettingsWrapper,
    environment: Environment,
    flagsmith_environments_v2_table: Table,
    feature: Feature,
    feature_state: FeatureState,
) -> None:
    # Given
    settings.ENVIRONMENTS_V2_TABLE_NAME_DYNAMO = flagsmith_environments_v2_table.name
    wrapper = DynamoEnvironmentV2Wrapper()

    identity_uuid = str(uuid.uuid4())
    identifier = "identity1"
    override_document_data = map_identity_override_to_identity_override_document(
        IdentityOverrideV2.parse_obj(
            {
                "environment_id": str(environment.id),
                "document_key": f"identity_override:{feature.id}:{identity_uuid}",
                "environment_api_key": environment.api_key,
                "feature_state": map_feature_state_to_engine(feature_state),
                "identifier": identifier,
                "identity_uuid": identity_uuid,
            }
        )
    )

    flagsmith_environments_v2_table.put_item(Item=override_document_data)

    override_document = IdentityOverrideV2.parse_obj(override_document_data)

    # When
    wrapper.update_identity_overrides(
        changeset=IdentityOverridesV2Changeset(
            to_delete=[override_document],
            to_put=[],
        ),
    )

    # Then
    results = flagsmith_environments_v2_table.scan()["Items"]
    assert len(results) == 0


def test_environment_v2_wrapper__write_environments__put_expected(
    settings: SettingsWrapper,
    environment: Environment,
    flagsmith_environments_v2_table: Table,
) -> None:
    # Given
    settings.ENVIRONMENTS_V2_TABLE_NAME_DYNAMO = flagsmith_environments_v2_table.name
    wrapper = DynamoEnvironmentV2Wrapper()

    # When
    wrapper.write_environments(
        environments=[environment],
    )

    # Then
    results = flagsmith_environments_v2_table.scan()["Items"]
    assert len(results) == 1
    assert results[0] == map_environment_to_environment_v2_document(environment)
