import typing

import pytest
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from pytest_django.fixtures import SettingsWrapper

from environments.dynamodb import (
    DynamoEnvironmentV2Wrapper,
    DynamoEnvironmentWrapper,
    DynamoIdentityWrapper,
)
from environments.models import Environment
from util.mappers import (
    map_environment_to_environment_document,
    map_environment_to_environment_v2_document,
)


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if metafunc.definition.get_closest_marker("valid_identity_identifiers"):
        metafunc.parametrize(
            "identifier",
            [
                "bond...jamesbond",
                "ゴジラ",
                "ElChapulínColorado",
                "dalek#6453@skaro.gov",
                "agáta={^_^}=",
                "_ツ_/-handless-shrug",
                "who+am+i?",
                "i_100%_dont_know!",
                "~neo|simulation`0065192*75`",
                "KacperGustyr$Flagsmat",
            ],
        )

    if metafunc.definition.get_closest_marker("invalid_identity_identifiers"):
        error_message = "Identifier can only contain unicode letters, numbers, and the symbols: ! # $ % & * + / = ? ^ _ ` { } | ~ @ . -"
        metafunc.parametrize(
            ["identifier", "identifier_error_message"],
            [
                ("", "This field may not be blank."),
                (" ", "This field may not be blank."),
                ("or really anything with a whitespace", error_message),
                ("<script>alert(1)</script>", error_message),
                ("'; DROP TABLE users;--", error_message),
                ("'single-quotes'", error_message),
                ('"double-quotes"', error_message),
                ("figaro" * 334, "Ensure this field has no more than 2000 characters."),
            ],
        )


@pytest.fixture()
def edge_identity_dynamo_wrapper_mock(mocker):  # type: ignore[no-untyped-def]
    return mocker.patch(
        "edge_api.identities.models.EdgeIdentity.dynamo_wrapper",
    )


@pytest.fixture()
def flagsmith_environment_api_key_table(dynamodb: "DynamoDBServiceResource") -> "Table":
    return dynamodb.create_table(
        TableName="flagsmith_environment_api_key",
        KeySchema=[{"AttributeName": "key", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "key", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )


@pytest.fixture()
def flagsmith_environment_table(dynamodb: "DynamoDBServiceResource") -> "Table":
    return dynamodb.create_table(
        TableName="flagsmith_environments",
        KeySchema=[{"AttributeName": "api_key", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "api_key", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )


@pytest.fixture()
def flagsmith_project_metadata_table(dynamodb: "DynamoDBServiceResource") -> "Table":
    return dynamodb.create_table(
        TableName="flagsmith_project_metadata",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "N"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )


@pytest.fixture
def dynamodb_identity_wrapper(
    settings: SettingsWrapper,
    flagsmith_identities_table: Table,
) -> DynamoIdentityWrapper:
    settings.IDENTITIES_TABLE_NAME_DYNAMO = flagsmith_identities_table.name
    return DynamoIdentityWrapper()


@pytest.fixture
def dynamodb_wrapper_v2(
    settings: SettingsWrapper,
    flagsmith_environments_v2_table: Table,
) -> DynamoEnvironmentV2Wrapper:
    settings.ENVIRONMENTS_V2_TABLE_NAME_DYNAMO = flagsmith_environments_v2_table.name
    return DynamoEnvironmentV2Wrapper()


@pytest.fixture()
def dynamo_enabled_project_environment_one_document(
    flagsmith_environment_table: Table,
    flagsmith_environments_v2_table: Table,
    dynamo_enabled_project_environment_one: Environment,
) -> dict[str, typing.Any]:
    environment_dict = map_environment_to_environment_document(
        dynamo_enabled_project_environment_one
    )
    flagsmith_environment_table.put_item(
        Item=environment_dict,
    )

    flagsmith_environments_v2_table.put_item(
        Item=map_environment_to_environment_v2_document(
            dynamo_enabled_project_environment_one
        )
    )

    return environment_dict


@pytest.fixture()
def dynamo_environment_wrapper(
    flagsmith_environment_table: Table,
    settings: SettingsWrapper,
) -> DynamoEnvironmentWrapper:
    settings.ENVIRONMENTS_TABLE_NAME_DYNAMO = flagsmith_environment_table.name
    wrapper = DynamoEnvironmentWrapper()
    wrapper.table_name = flagsmith_environment_table.name
    return wrapper
