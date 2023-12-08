import os
import uuid

import boto3
import pytest
from moto import mock_dynamodb
from mypy_boto3_dynamodb.service_resource import Table
from pytest_django.fixtures import SettingsWrapper

from environments.dynamodb.dynamodb_wrapper import DynamoEnvironmentV2Wrapper
from environments.models import Environment
from features.models import Feature
from util.mappers.dynamodb import map_environment_to_environment_v2_document


@pytest.fixture()
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"


@pytest.fixture()
def dynamodb(aws_credentials):
    # TODO: move all wrapper tests to using moto
    with mock_dynamodb():
        yield boto3.resource("dynamodb")


@pytest.fixture()
def flagsmith_environments_table(dynamodb):
    return dynamodb.create_table(
        TableName="flagsmith_environments_v2",
        KeySchema=[
            {
                "AttributeName": "environment_id",
                "KeyType": "HASH",
            },
            {
                "AttributeName": "document_key",
                "KeyType": "RANGE",
            },
        ],
        AttributeDefinitions=[
            {"AttributeName": "environment_id", "AttributeType": "N"},
            {"AttributeName": "document_key", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )


def test_environment_v2_wrapper_get_identity_overrides(
    settings: SettingsWrapper,
    environment: Environment,
    flagsmith_environments_table: Table,
    feature: Feature,
) -> None:
    # Given
    settings.ENVIRONMENTS_V2_TABLE_NAME_DYNAMO = flagsmith_environments_table.name
    wrapper = DynamoEnvironmentV2Wrapper()

    identity_uuid = str(uuid.uuid4())
    identifier = "identity1"
    override_document = {
        "environment_id": environment.id,
        "document_key": f"identity_override:{feature.id}:{identity_uuid}",
        "environment_api_key": environment.api_key,
        "identifier": identifier,
        "feature_state": {},
    }

    environment_document = map_environment_to_environment_v2_document(environment)

    flagsmith_environments_table.put_item(Item=override_document)
    flagsmith_environments_table.put_item(Item=environment_document)

    # When
    results = wrapper.get_identity_overrides(environment_id=environment.id)

    # Then
    assert len(results) == 1
    assert results[0] == override_document
