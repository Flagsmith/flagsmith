import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, List, Optional

import pytest
from flag_engine.features.models import (
    MultivariateFeatureOptionModel,
    MultivariateFeatureStateValueList,
    MultivariateFeatureStateValueModel,
)
from pydantic import BaseModel, Field
from pytest_mock import MockerFixture

from mappers import dynamodb

if TYPE_CHECKING:  # pragma: no cover
    from environments.identities.models import Identity
    from environments.models import Environment, EnvironmentAPIKey


@pytest.fixture
def mock_engine_model() -> BaseModel:
    class TestModel(BaseModel):
        field: str

    return TestModel(field="foobar")


def test_map_environment_to_environment_document__call_expected(
    environment: "Environment",
    mocker: MockerFixture,
    mock_engine_model: BaseModel,
) -> None:
    # Given
    map_environment_to_engine_mock = mocker.patch(
        "mappers.dynamodb.map_environment_to_engine"
    )
    map_value_to_document_value_mock = mocker.patch(
        "mappers.dynamodb._map_value_to_document_value"
    )
    map_environment_to_engine_mock.return_value = mock_engine_model
    map_value_to_document_value_mock.return_value = "foobar"

    # When
    result = dynamodb.map_environment_to_environment_document(environment)

    # Then
    assert result == {"field": "foobar"}
    map_environment_to_engine_mock.assert_called_once_with(environment)
    map_value_to_document_value_mock.assert_called_once_with(mock_engine_model.field)


def test_map_environment_api_key_to_environment_api_key_document__call_expected(
    environment_api_key: "EnvironmentAPIKey",
    mocker: MockerFixture,
    mock_engine_model: BaseModel,
) -> None:
    # Given
    map_environment_api_key_to_engine_mock = mocker.patch(
        "mappers.dynamodb.map_environment_api_key_to_engine"
    )
    map_value_to_document_value_mock = mocker.patch(
        "mappers.dynamodb._map_value_to_document_value"
    )
    map_environment_api_key_to_engine_mock.return_value = mock_engine_model
    map_value_to_document_value_mock.return_value = "foobar"

    # When
    result = dynamodb.map_environment_api_key_to_environment_api_key_document(
        environment_api_key,
    )

    # Then
    assert result == {"field": "foobar"}
    map_environment_api_key_to_engine_mock.assert_called_once_with(environment_api_key)
    map_value_to_document_value_mock.assert_called_once_with(mock_engine_model.field)


def test_map_engine_identity_to_identity_document__call_expected(
    mocker: MockerFixture,
    mock_engine_model: BaseModel,
) -> None:
    # Given
    map_value_to_document_value_mock = mocker.patch(
        "mappers.dynamodb._map_value_to_document_value"
    )
    map_value_to_document_value_mock.return_value = "foobar"

    # When
    result = dynamodb.map_engine_identity_to_identity_document(
        mock_engine_model,
    )

    # Then
    assert result == {"field": "foobar"}
    map_value_to_document_value_mock.assert_called_once_with(mock_engine_model.field)


def test_map_identity_to_identity_document__call_expected(
    identity: "Identity",
    mocker: MockerFixture,
    mock_engine_model: BaseModel,
) -> None:
    # Given
    document = {"field": "foobar"}
    map_identity_to_engine_mock = mocker.patch(
        "mappers.dynamodb.map_identity_to_engine"
    )
    map_engine_identity_to_identity_document_mock = mocker.patch(
        "mappers.dynamodb.map_engine_identity_to_identity_document"
    )
    map_identity_to_engine_mock.return_value = mock_engine_model
    map_engine_identity_to_identity_document_mock.return_value = document

    # When
    result = dynamodb.map_identity_to_identity_document(identity)

    # Then
    assert result == document
    map_identity_to_engine_mock.assert_called_once_with(identity)
    map_engine_identity_to_identity_document_mock.assert_called_once_with(
        mock_engine_model,
    )


def test_map_value_to_document_value__return_expected() -> None:
    # Given
    now = datetime.now()
    uuid_value = uuid.uuid4()

    class Unknown:
        def __str__(self) -> str:
            return "bing"

    class TestModel(BaseModel):
        value_list: Optional[List[Any]] = None
        value: str = Field(default_factory=lambda: "pydantic works")

    value_list = [
        TestModel(value_list=[12.2, False, {"key": [TestModel()], "uuid": uuid_value}]),
        None,
        True,
        now,
        "as is",
        42,
        Unknown(),
    ]

    mv_fs_value = MultivariateFeatureStateValueModel(
        percentage_allocation=50,
        multivariate_feature_option=MultivariateFeatureOptionModel(
            value="foobar",
        ),
    )
    custom_engine_container = MultivariateFeatureStateValueList([mv_fs_value])

    model = TestModel(value_list=value_list, value="outer_value")
    value = {
        "outer_key": model,
        "uuid": uuid_value,
        "custom_list": custom_engine_container,
    }

    expected_value = {
        "outer_key": {
            "value": "outer_value",
            "value_list": [
                {
                    "value": "pydantic works",
                    "value_list": [
                        Decimal("12.2"),
                        False,
                        {
                            "key": [{"value": "pydantic works", "value_list": None}],
                            "uuid": str(uuid_value),
                        },
                    ],
                },
                None,
                True,
                now.isoformat(),
                "as is",
                Decimal("42"),
                "bing",
            ],
        },
        "uuid": str(uuid_value),
        "custom_list": [
            {
                "id": None,
                "multivariate_feature_option": {"id": None, "value": "foobar"},
                "mv_fs_value_uuid": str(mv_fs_value.mv_fs_value_uuid),
                "percentage_allocation": Decimal("50.0"),
            }
        ],
    }

    # When
    result = dynamodb._map_value_to_document_value(value)

    # Then
    assert result == expected_value
