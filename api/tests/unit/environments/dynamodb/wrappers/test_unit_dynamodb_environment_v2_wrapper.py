import uuid
from typing import Any

from boto3.dynamodb.types import Binary
from common.test_tools import AssertMetricFixture
from freezegun import freeze_time
from mypy_boto3_dynamodb.service_resource import Table
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from environments.dynamodb import DynamoEnvironmentV2Wrapper
from environments.dynamodb.types import (
    IdentityOverridesV2Changeset,
    IdentityOverrideV2,
)
from environments.dynamodb.utils import (
    get_environments_v2_identity_override_document_key,
)
from environments.models import Environment
from features.models import Feature, FeatureState
from tests.types import EnableFeaturesFixture
from util.mappers import (
    map_environment_to_environment_v2_document,
    map_feature_state_to_engine,
    map_identity_override_to_identity_override_document,
)


def test_environment_v2_wrapper__get_identity_overrides_by_environment_id__return_expected(  # noqa: FT004
    environment: Environment,
    dynamodb_wrapper_v2: DynamoEnvironmentV2Wrapper,
    feature: Feature,
    identity_override_document: dict[str, Any],
) -> None:
    # When
    results = dynamodb_wrapper_v2.get_identity_overrides_by_environment_id(
        environment_id=environment.id,
        feature_id=feature.id,
    )

    # Then
    assert len(results) == 1
    assert results[0] == identity_override_document


def test_environment_v2_wrapper__get_identity_overrides_by_environment_id__last_evaluated_key__call_expected(  # noqa: FT003
    flagsmith_environments_v2_table: Table,
    mocker: MockerFixture,
) -> None:
    # Given
    wrapper = DynamoEnvironmentV2Wrapper()
    mocker.patch.object(wrapper, "get_table").return_value = table_mock = (
        mocker.MagicMock(spec=flagsmith_environments_v2_table)
    )

    last_evaluated_key = "next_page_key"
    override_document = {"test": "document"}

    table_mock.query.side_effect = [
        {"Items": [override_document], "LastEvaluatedKey": last_evaluated_key},
        {"Items": [override_document], "LastEvaluatedKey": None},
    ]

    # When
    results = wrapper.get_identity_overrides_by_environment_id(
        environment_id=mocker.ANY,
        feature_id=mocker.ANY,
    )

    # Then
    assert results == [override_document, override_document]
    wrapper.table.query.assert_has_calls(  # type: ignore[union-attr]
        [
            mocker.call(
                KeyConditionExpression=mocker.ANY,
            ),
            mocker.call(
                KeyConditionExpression=mocker.ANY,
                ExclusiveStartKey=last_evaluated_key,
            ),
        ]
    )


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
            "document_key": get_environments_v2_identity_override_document_key(
                feature_id=feature.id, identity_uuid=identity_uuid
            ),
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


@freeze_time("2023-01-01T00:00:00Z")
def test_environment_v2_wrapper__update_identity_overrides__put__stores_created_date(  # noqa: FT003
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
    override_document = IdentityOverrideV2.parse_obj(
        {
            "environment_id": str(environment.id),
            "document_key": get_environments_v2_identity_override_document_key(
                feature_id=feature.id, identity_uuid=identity_uuid
            ),
            "environment_api_key": environment.api_key,
            "feature_state": map_feature_state_to_engine(feature_state),
            "identifier": "identity1",
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
    assert results[0]["created_date"] == "2023-01-01T00:00:00+00:00"


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
                "document_key": get_environments_v2_identity_override_document_key(
                    feature_id=feature.id, identity_uuid=identity_uuid
                ),
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


def test_environment_v2_wrapper__write_environments__compress_dynamo_documents_enabled__writes_compressed(  # noqa: FT003
    environment: Environment,
    dynamodb_wrapper_v2: DynamoEnvironmentV2Wrapper,
    flagsmith_environments_v2_table: Table,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("compress_dynamo_documents")

    # When
    dynamodb_wrapper_v2.write_environments([environment])

    # Then
    results = flagsmith_environments_v2_table.scan()["Items"]
    assert len(results) == 1
    assert results[0]["compressed"] is True
    assert isinstance(results[0]["project"], Binary)
    assert isinstance(results[0]["feature_states"], Binary)


def test_environment_v2_wrapper__write_environments__compress_dynamo_documents_enabled__observes_metrics(  # noqa: FT003
    environment: Environment,
    dynamodb_wrapper_v2: DynamoEnvironmentV2Wrapper,
    flagsmith_environments_v2_table: Table,
    enable_features: EnableFeaturesFixture,
    assert_metric: AssertMetricFixture,
) -> None:
    # Given
    enable_features("compress_dynamo_documents")

    # When
    dynamodb_wrapper_v2.write_environments([environment])

    # Then
    assert_metric(
        name="flagsmith_dynamo_environment_document_size_bytes_count",
        labels={"table": flagsmith_environments_v2_table.name, "compressed": "true"},
        value=1.0,
    )
    assert_metric(
        name="flagsmith_dynamo_environment_document_compression_ratio_count",
        labels={"table": flagsmith_environments_v2_table.name},
        value=1.0,
    )


def test_environment_v2_wrapper__write_environments__uncompressed__observes_size_metric(  # noqa: FT003,FT004
    environment: Environment,
    dynamodb_wrapper_v2: DynamoEnvironmentV2Wrapper,
    flagsmith_environments_v2_table: Table,
    assert_metric: AssertMetricFixture,
) -> None:
    # When
    dynamodb_wrapper_v2.write_environments([environment])

    # Then
    assert_metric(
        name="flagsmith_dynamo_environment_document_size_bytes_count",
        labels={"table": flagsmith_environments_v2_table.name, "compressed": "false"},
        value=1.0,
    )


def test_environment_v2_wrapper__write_environments__compress_dynamo_documents_enabled__logs_expected(  # noqa: FT003
    environment: Environment,
    dynamodb_wrapper_v2: DynamoEnvironmentV2Wrapper,
    flagsmith_environments_v2_table: Table,
    enable_features: EnableFeaturesFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    enable_features("compress_dynamo_documents")

    # When
    dynamodb_wrapper_v2.write_environments([environment])

    # Then
    assert log.events == [
        {
            "environment_api_key": environment.api_key,
            "environment_id": environment.id,
            "event": "environment-document-compressed",
            "level": "info",
        },
    ]


def test_environment_v2_wrapper__delete_environment__deletes_related_data_from_dynamodb(
    flagsmith_environments_v2_table: Table,
    dynamodb_wrapper_v2: DynamoEnvironmentV2Wrapper,
) -> None:
    # Given
    environment_api_key = "api_key"
    environment_id = "10"

    # Add some items to the table
    for i in range(10):
        flagsmith_environments_v2_table.put_item(
            Item={
                "environment_api_key": environment_api_key,
                "environment_id": environment_id,
                "document_key": get_environments_v2_identity_override_document_key(
                    feature_id=i,
                ),
            }
        )

    # Next, let's add an item for a different environment
    environment_2_api_key = "different_api_key"
    environment_2_id = "11"
    flagsmith_environments_v2_table.put_item(
        Item={
            "environment_api_key": environment_2_api_key,
            "environment_id": environment_2_id,
            "document_key": get_environments_v2_identity_override_document_key(
                feature_id=1,
            ),
        }
    )

    # When
    dynamodb_wrapper_v2.delete_environment(environment_id=environment_id)  # type: ignore[arg-type]

    # Then
    results = flagsmith_environments_v2_table.scan()["Items"]
    assert len(results) == 1
    assert results[0] == {
        "environment_api_key": environment_2_api_key,
        "environment_id": environment_2_id,
        "document_key": get_environments_v2_identity_override_document_key(
            feature_id=1,
        ),
    }
