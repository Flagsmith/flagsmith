import typing
from decimal import Decimal

import pytest
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from django.core.exceptions import ObjectDoesNotExist
from mypy_boto3_dynamodb.service_resource import Table
from pytest_mock import MockerFixture
from rest_framework.exceptions import NotFound

from edge_api.identities.search import (
    IDENTIFIER_ATTRIBUTE,
    EdgeIdentitySearchData,
    EdgeIdentitySearchType,
)
from environments.dynamodb import DynamoIdentityWrapper
from environments.dynamodb.wrappers.exceptions import (
    CapacityBudgetExceeded,
    SystemTraitWriteRaceError,
)
from environments.identities.models import Identity
from environments.identities.traits.constants import (
    TRAIT_STRING_VALUE_MAX_LENGTH,
)
from util.mappers import (
    map_identity_to_identity_document,
)

if typing.TYPE_CHECKING:
    pass


def test_get_item_from_uuid__valid_uuid__calls_query_correctly(mocker):  # type: ignore[no-untyped-def]
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")
    identity_uuid = "test_uuid"

    # When
    dynamo_identity_wrapper.get_item_from_uuid(identity_uuid)
    # Then
    mocked_dynamo_table.query.assert_called_with(
        IndexName="identity_uuid-index",
        Limit=1,
        KeyConditionExpression=Key("identity_uuid").eq(identity_uuid),
    )


def test_get_item_from_uuid__identity_not_found__raises_object_does_not_exist(  # type: ignore[no-untyped-def]
    mocker,
):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")
    mocked_dynamo_table.query.return_value = {"Items": [], "Count": 0}

    # When / Then
    with pytest.raises(ObjectDoesNotExist):
        dynamo_identity_wrapper.get_item_from_uuid("identity_uuid")


def test_get_item_from_uuid_or_404__existing_identity__returns_document(  # type: ignore[no-untyped-def]
    mocker,
):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    expected_document = {"key": "value"}
    mocked_get_item_from_uuid = mocker.patch.object(
        dynamo_identity_wrapper, "get_item_from_uuid", return_value=expected_document
    )
    identity_uuid = "test_uuid"

    # When
    returned_document = dynamo_identity_wrapper.get_item_from_uuid_or_404(identity_uuid)

    # Then
    assert returned_document == expected_document
    mocked_get_item_from_uuid.assert_called_with(identity_uuid)


def test_get_item_from_uuid_or_404__identity_not_found__raises_not_found(  # type: ignore[no-untyped-def]
    mocker,
):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    mocker.patch.object(
        dynamo_identity_wrapper, "get_item_from_uuid", side_effect=ObjectDoesNotExist
    )
    identity_uuid = "test_uuid"

    # When / Then
    with pytest.raises(NotFound):
        dynamo_identity_wrapper.get_item_from_uuid_or_404(identity_uuid)


def test_delete_item__valid_composite_key__calls_dynamo_correctly(mocker):  # type: ignore[no-untyped-def]
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    composite_key = "test_key"
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")

    # When
    dynamo_identity_wrapper.delete_item(composite_key)

    # Then
    mocked_dynamo_table.delete_item.assert_called_with(
        Key={"composite_key": composite_key}
    )


def test_get_item__valid_composite_key__calls_dynamo_correctly(mocker):  # type: ignore[no-untyped-def]
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    composite_key = "test_key"
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")

    # When
    dynamo_identity_wrapper.get_item(composite_key)

    # Then
    mocked_dynamo_table.get_item.assert_called_with(
        Key={"composite_key": composite_key}
    )


def test_get_all_items__without_start_key__calls_query_correctly(mocker):  # type: ignore[no-untyped-def]
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    environment_key = "environment_key"
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")

    # When
    dynamo_identity_wrapper.get_all_items(environment_key, 999)

    # Then
    mocked_dynamo_table.query.assert_called_with(
        IndexName="environment_api_key-identifier-index",
        Limit=999,
        KeyConditionExpression=Key("environment_api_key").eq(environment_key),
    )


def test_get_all_items__with_start_key__calls_query_correctly(mocker):  # type: ignore[no-untyped-def]
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()

    environment_key = "environment_key"
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")
    start_key = {"key": "value"}

    # When
    dynamo_identity_wrapper.get_all_items(environment_key, 999, start_key)  # type: ignore[arg-type]

    # Then
    mocked_dynamo_table.query.assert_called_with(
        IndexName="environment_api_key-identifier-index",
        Limit=999,
        KeyConditionExpression=Key("environment_api_key").eq(environment_key),
        ExclusiveStartKey=start_key,
    )


def test_get_all_items__return_consumed_capacity_true__calls_expected(
    mocker: MockerFixture,
) -> None:
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()

    environment_key = "environment_key"
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")

    # When
    dynamo_identity_wrapper.get_all_items(
        environment_api_key=environment_key,
        limit=999,
        return_consumed_capacity=True,
    )

    # Then
    mocked_dynamo_table.query.assert_called_with(
        IndexName="environment_api_key-identifier-index",
        Limit=999,
        KeyConditionExpression=Key("environment_api_key").eq(environment_key),
        ReturnConsumedCapacity="TOTAL",
    )


def test_search_items__with_identifier__calls_query_correctly(mocker):  # type: ignore[no-untyped-def]
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    environment_key = "environment_key"
    identifier = "test_user"
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")
    start_key = {"key": "value"}
    search_function = lambda x: Key("identifier").eq(x)  # noqa: E731

    # When
    dynamo_identity_wrapper.search_items(
        environment_key,
        EdgeIdentitySearchData(
            search_term=identifier,
            search_type=EdgeIdentitySearchType.EQUAL,
            search_attribute=IDENTIFIER_ATTRIBUTE,
        ),
        999,
        start_key,
    )

    # Then
    mocked_dynamo_table.query.assert_called_with(
        IndexName="environment_api_key-identifier-index",
        Limit=999,
        KeyConditionExpression=Key("environment_api_key").eq(environment_key)
        & search_function(identifier),  # type: ignore[no-untyped-call]
        ExclusiveStartKey=start_key,
    )


def test_write_identities__single_identity__calls_batch_writer_correctly(  # type: ignore[no-untyped-def]
    mocker, project, identity
):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")

    expected_identity_document = map_identity_to_identity_document(identity)
    identities = Identity.objects.filter(id=identity.id)

    # When
    dynamo_identity_wrapper.write_identities(identities)

    # Then
    mocked_dynamo_table.batch_writer.assert_called_with()

    mocked_put_item = (
        mocked_dynamo_table.batch_writer.return_value.__enter__.return_value.put_item
    )
    _, kwargs = mocked_put_item.call_args
    actual_identity_document = kwargs["Item"]

    # Remove identity_uuid from the document since it will be different
    actual_identity_document.pop("identity_uuid")
    expected_identity_document.pop("identity_uuid")

    assert actual_identity_document == expected_identity_document


def test_write_identities__identifier_too_large__skips_identity(  # type: ignore[no-untyped-def]
    mocker, project, identity
):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")

    # Let's make the identifier too long
    identity.identifier = "a" * 1025
    identity.save()

    identities = Identity.objects.filter(id=identity.id)

    # When
    dynamo_identity_wrapper.write_identities(identities)

    # Then
    mocked_dynamo_table.batch_writer.assert_called_with()
    mocked_dynamo_table.batch_writer.return_value.__enter__.return_value.put_item.assert_not_called()


def test_is_enabled__table_name_not_set__returns_false(settings, mocker):  # type: ignore[no-untyped-def]
    # Given
    mocker.patch(
        "environments.dynamodb.wrappers.identity_wrapper.DynamoIdentityWrapper.table_name",
        None,
    )
    mocked_boto3 = mocker.patch("environments.dynamodb.wrappers.base.boto3")

    # When
    dynamo_identity_wrapper = DynamoIdentityWrapper()

    # Then
    assert dynamo_identity_wrapper.is_enabled is False
    mocked_boto3.resource.assert_not_called()
    mocked_boto3.resource.return_value.Table.assert_not_called()


def test_is_enabled__table_name_set__returns_true(settings, mocker):  # type: ignore[no-untyped-def]
    # Given
    table_name = "random_table_name"
    settings.IDENTITIES_TABLE_NAME_DYNAMO = table_name
    mocked_config = mocker.patch("environments.dynamodb.wrappers.base.Config")
    mocked_boto3 = mocker.patch("environments.dynamodb.wrappers.base.boto3")

    # When
    dynamo_identity_wrapper = DynamoIdentityWrapper()

    # Then
    assert dynamo_identity_wrapper.is_enabled is True
    mocked_boto3.resource.assert_called_with(
        "dynamodb", config=mocked_config(tcp_keepalive=True)
    )
    mocked_boto3.resource.return_value.Table.assert_called_with(table_name)


def test_set_system_trait__oversized_string_value__raises() -> None:
    # Given
    wrapper = DynamoIdentityWrapper()

    # When / Then
    with pytest.raises(ValueError):
        wrapper.set_system_trait(
            environment_api_key="key",
            identifier="user",
            trait_key="flagsmith_cohort_a",
            trait_value="x" * (TRAIT_STRING_VALUE_MAX_LENGTH + 1),
        )


def test_identity_wrapper__iter_all_items_paginated__returns_expected(
    identity: "Identity",
    mocker: "MockerFixture",
) -> None:
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    identity_document = map_identity_to_identity_document(identity)
    environment_api_key = "test_api_key"
    limit = 1

    expected_next_page_key = "next_page_key"

    mocked_get_all_items = mocker.patch.object(
        dynamo_identity_wrapper,
        "get_all_items",
        autospec=True,
    )
    mocked_get_all_items.side_effect = [
        {"Items": [identity_document], "LastEvaluatedKey": "next_page_key"},
        {"Items": [identity_document], "LastEvaluatedKey": None},
    ]

    # When
    iterator = dynamo_identity_wrapper.iter_all_items_paginated(
        environment_api_key=environment_api_key, limit=limit
    )
    result_1 = next(iterator)
    result_2 = next(iterator)

    # Then
    with pytest.raises(StopIteration):
        next(iterator)

    assert result_1 == identity_document
    assert result_2 == identity_document

    mocked_get_all_items.assert_has_calls(
        [
            mocker.call(
                environment_api_key=environment_api_key,
                limit=limit,
                projection_expression=None,
                return_consumed_capacity=False,
            ),
            mocker.call(
                environment_api_key=environment_api_key,
                limit=limit,
                projection_expression=None,
                return_consumed_capacity=False,
                start_key=expected_next_page_key,
            ),
        ]
    )


@pytest.mark.parametrize("capacity_budget", [Decimal("2.0"), Decimal("2.2")])
def test_iter_all_items_paginated__capacity_budget_exceeded__raises_expected(
    identity: "Identity",
    mocker: "MockerFixture",
    capacity_budget: Decimal,
) -> None:
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    identity_document = map_identity_to_identity_document(identity)
    environment_api_key = "test_api_key"
    limit = 1

    expected_next_page_key = "next_page_key"

    mocked_get_all_items = mocker.patch.object(
        dynamo_identity_wrapper,
        "get_all_items",
        autospec=True,
    )
    mocked_get_all_items.side_effect = [
        {
            "Items": [identity_document],
            "LastEvaluatedKey": "next_page_key",
            "ConsumedCapacity": {"CapacityUnits": Decimal("1.1")},
        },
        {
            "Items": [identity_document],
            "LastEvaluatedKey": "next_after_next_page_key",
            "ConsumedCapacity": {"CapacityUnits": Decimal("1.1")},
        },
        {
            "Items": [identity_document],
            "LastEvaluatedKey": None,
            "ConsumedCapacity": {"CapacityUnits": Decimal("1.1")},
        },
    ]

    # When
    iterator = dynamo_identity_wrapper.iter_all_items_paginated(
        environment_api_key=environment_api_key,
        limit=limit,
        capacity_budget=capacity_budget,
    )
    result_1 = next(iterator)
    result_2 = next(iterator)

    # Then
    with pytest.raises(CapacityBudgetExceeded) as exc_info:
        next(iterator)

    assert result_1 == identity_document
    assert result_2 == identity_document
    assert exc_info.value.capacity_budget == capacity_budget
    assert exc_info.value.capacity_spent == Decimal("2.2")

    mocked_get_all_items.assert_has_calls(
        [
            mocker.call(
                environment_api_key=environment_api_key,
                limit=limit,
                projection_expression=None,
                return_consumed_capacity=True,
            ),
            mocker.call(
                environment_api_key=environment_api_key,
                limit=limit,
                projection_expression=None,
                return_consumed_capacity=True,
                start_key=expected_next_page_key,
            ),
        ]
    )


def test_delete_all_identities__multiple_identities__deletes_only_matching_environment(
    flagsmith_identities_table: Table,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    environment_api_key = "environment_one"

    # Let's create 2 identities for the same environment
    identity_one = {
        "composite_key": f"{environment_api_key}_identity_one",
        "environment_api_key": environment_api_key,
        "identifier": "identity_one",
    }
    identity_two = {
        "composite_key": f"{environment_api_key}_identity_two",
        "identifier": "identity_two",
        "environment_api_key": environment_api_key,
    }

    flagsmith_identities_table.put_item(Item=identity_one)
    flagsmith_identities_table.put_item(Item=identity_two)

    # Let's create another identity for a different environment
    identity_three = {
        "composite_key": "environment_two_identity_one",
        "identifier": "identity_three",
        "environment_api_key": "environment_two",
    }
    flagsmith_identities_table.put_item(Item=identity_three)

    # When
    dynamodb_identity_wrapper.delete_all_identities(environment_api_key)

    # Then
    assert flagsmith_identities_table.scan()["Count"] == 1
    assert flagsmith_identities_table.scan()["Items"][0] == identity_three


def test_set_system_trait__document_with_system_traits__sets_only_given_key(
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    dynamodb_identity_wrapper.put_item(
        {
            "composite_key": "api-key_user-1",
            "identifier": "user-1",
            "environment_api_key": "api-key",
            "identity_traits": [{"trait_key": "plan", "trait_value": "pro"}],
            "system_traits": {"other": True},
        }
    )

    # When
    dynamodb_identity_wrapper.set_system_trait(
        environment_api_key="api-key", identifier="user-1", trait_key="cohort_x"
    )

    # Then
    document = dynamodb_identity_wrapper.get_item("api-key_user-1")
    assert document is not None
    assert document["system_traits"] == {"other": True, "cohort_x": True}
    assert document["identity_traits"] == [{"trait_key": "plan", "trait_value": "pro"}]


def test_set_system_trait__document_without_system_traits__creates_system_traits(
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    dynamodb_identity_wrapper.put_item(
        {
            "composite_key": "api-key_user-1",
            "identifier": "user-1",
            "environment_api_key": "api-key",
        }
    )
    read_spy = mocker.spy(dynamodb_identity_wrapper.table, "get_item")

    # When
    dynamodb_identity_wrapper.set_system_trait(
        environment_api_key="api-key", identifier="user-1", trait_key="cohort_x"
    )

    # Then
    assert read_spy.call_count == 1
    document = dynamodb_identity_wrapper.get_item("api-key_user-1")
    assert document is not None
    assert document["system_traits"] == {"cohort_x": True}


def test_set_system_trait__null_system_traits__replaces_with_map(
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given - a document written with `system_traits: null` by another service
    dynamodb_identity_wrapper.put_item(
        {
            "composite_key": "api-key_user-1",
            "identifier": "user-1",
            "environment_api_key": "api-key",
            "identity_traits": [{"trait_key": "plan", "trait_value": "pro"}],
            "system_traits": None,
        }
    )

    # When
    dynamodb_identity_wrapper.set_system_trait(
        environment_api_key="api-key", identifier="user-1", trait_key="cohort_x"
    )

    # Then
    document = dynamodb_identity_wrapper.get_item("api-key_user-1")
    assert document is not None
    assert document["system_traits"] == {"cohort_x": True}
    assert document["identity_traits"] == [{"trait_key": "plan", "trait_value": "pro"}]


def test_set_system_trait__missing_document__creates_document(
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    composite_key = "api-key_user-1"

    # When
    dynamodb_identity_wrapper.set_system_trait(
        environment_api_key="api-key", identifier="user-1", trait_key="cohort_x"
    )

    # Then
    document = dynamodb_identity_wrapper.get_item(composite_key)
    assert document is not None
    assert document["identifier"] == "user-1"
    assert document["system_traits"] == {"cohort_x": True}


def test_set_system_trait__system_traits_created_concurrently__merges_into_existing(
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    # The table holds a document whose system_traits appeared after the
    # wrapper's first read (simulated by a stale first response without them).
    dynamodb_identity_wrapper.put_item(
        {
            "composite_key": "api-key_user-1",
            "identifier": "user-1",
            "environment_api_key": "api-key",
            "system_traits": {"other": True},
        }
    )
    real_get_item = dynamodb_identity_wrapper.table.get_item  # type: ignore[union-attr]
    stale_responses: typing.Iterator[dict[str, typing.Any]] = iter(
        [
            {
                "Item": {
                    "composite_key": "api-key_user-1",
                    "identifier": "user-1",
                    "environment_api_key": "api-key",
                }
            }
        ]
    )
    mocker.patch.object(
        dynamodb_identity_wrapper.table,
        "get_item",
        side_effect=lambda **kwargs: next(stale_responses, real_get_item(**kwargs)),
    )

    # When
    dynamodb_identity_wrapper.set_system_trait(
        environment_api_key="api-key", identifier="user-1", trait_key="cohort_x"
    )

    # Then
    document = real_get_item(Key={"composite_key": "api-key_user-1"})["Item"]
    assert document["system_traits"] == {"other": True, "cohort_x": True}


def test_set_system_trait__custom_trait_value__written_to_document(
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    dynamodb_identity_wrapper.put_item(
        {
            "composite_key": "api-key_user-1",
            "identifier": "user-1",
            "environment_api_key": "api-key",
            "system_traits": {"cohort_x": True},
        }
    )

    # When
    dynamodb_identity_wrapper.set_system_trait(
        environment_api_key="api-key",
        identifier="user-1",
        trait_key="score",
        trait_value=0.5,
    )

    # Then
    document = dynamodb_identity_wrapper.get_item("api-key_user-1")
    assert document is not None
    assert document["system_traits"] == {"cohort_x": True, "score": Decimal("0.5")}


def test_set_system_trait__value_changed__overwrites(
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    dynamodb_identity_wrapper.put_item(
        {
            "composite_key": "api-key_user-1",
            "identifier": "user-1",
            "environment_api_key": "api-key",
            "system_traits": {"tier": "silver"},
        }
    )

    # When
    dynamodb_identity_wrapper.set_system_trait(
        environment_api_key="api-key",
        identifier="user-1",
        trait_key="tier",
        trait_value="gold",
    )

    # Then
    document = dynamodb_identity_wrapper.get_item("api-key_user-1")
    assert document is not None
    assert document["system_traits"] == {"tier": "gold"}


def test_set_system_trait__already_set__skips_write(
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    dynamodb_identity_wrapper.put_item(
        {
            "composite_key": "api-key_user-1",
            "identifier": "user-1",
            "environment_api_key": "api-key",
            "system_traits": {"cohort_x": True},
        }
    )
    update_mock = mocker.patch.object(dynamodb_identity_wrapper.table, "update_item")
    put_mock = mocker.patch.object(dynamodb_identity_wrapper.table, "put_item")

    # When
    dynamodb_identity_wrapper.set_system_trait(
        environment_api_key="api-key", identifier="user-1", trait_key="cohort_x"
    )

    # Then
    update_mock.assert_not_called()
    put_mock.assert_not_called()


def test_set_system_trait__stale_missing_document_read__retries_and_merges(
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    dynamodb_identity_wrapper.put_item(
        {
            "composite_key": "api-key_user-1",
            "identifier": "user-1",
            "environment_api_key": "api-key",
            "system_traits": {"other": True},
        }
    )
    real_get_item = dynamodb_identity_wrapper.table.get_item  # type: ignore[union-attr]
    stale_responses: typing.Iterator[dict[str, typing.Any]] = iter([{}])
    mocker.patch.object(
        dynamodb_identity_wrapper.table,
        "get_item",
        side_effect=lambda **kwargs: next(stale_responses, real_get_item(**kwargs)),
    )

    # When
    dynamodb_identity_wrapper.set_system_trait(
        environment_api_key="api-key", identifier="user-1", trait_key="cohort_x"
    )

    # Then
    document = real_get_item(Key={"composite_key": "api-key_user-1"})["Item"]
    assert document["system_traits"] == {"other": True, "cohort_x": True}


def test_set_system_trait__conditional_writes_keep_losing__raises(
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    dynamodb_identity_wrapper.put_item(
        {
            "composite_key": "api-key_user-1",
            "identifier": "user-1",
            "environment_api_key": "api-key",
        }
    )
    real_get_item = dynamodb_identity_wrapper.table.get_item  # type: ignore[union-attr]
    mocker.patch.object(dynamodb_identity_wrapper.table, "get_item", return_value={})

    # When
    with pytest.raises(SystemTraitWriteRaceError):
        dynamodb_identity_wrapper.set_system_trait(
            environment_api_key="api-key", identifier="user-1", trait_key="cohort_x"
        )

    # Then
    document = real_get_item(Key={"composite_key": "api-key_user-1"})["Item"]
    assert "system_traits" not in document


def test_set_system_trait__unexpected_client_error__reraises(
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch.object(
        dynamodb_identity_wrapper.table,
        "put_item",
        side_effect=ClientError({"Error": {"Code": "ValidationException"}}, "PutItem"),
    )

    # When
    with pytest.raises(ClientError) as exc_info:
        dynamodb_identity_wrapper.set_system_trait(
            environment_api_key="api-key", identifier="user-1", trait_key="cohort_x"
        )

    # Then
    assert exc_info.value.response["Error"]["Code"] == "ValidationException"


def test_unset_system_trait__member__removes_only_given_key(
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    dynamodb_identity_wrapper.put_item(
        {
            "composite_key": "api-key_user-1",
            "identifier": "user-1",
            "environment_api_key": "api-key",
            "identity_traits": [{"trait_key": "plan", "trait_value": "pro"}],
            "system_traits": {"cohort_x": True, "other": True},
        }
    )

    # When
    dynamodb_identity_wrapper.unset_system_trait(
        environment_api_key="api-key", identifier="user-1", trait_key="cohort_x"
    )

    # Then
    document = dynamodb_identity_wrapper.get_item("api-key_user-1")
    assert document is not None
    assert document["system_traits"] == {"other": True}
    assert document["identity_traits"] == [{"trait_key": "plan", "trait_value": "pro"}]


def test_unset_system_trait__missing_document__no_ghost_document(
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    composite_key = "api-key_never-seen"

    # When
    dynamodb_identity_wrapper.unset_system_trait(
        environment_api_key="api-key", identifier="never-seen", trait_key="cohort_x"
    )

    # Then
    assert dynamodb_identity_wrapper.get_item(composite_key) is None


def test_unset_system_trait__unexpected_client_error__reraises(
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch.object(
        dynamodb_identity_wrapper.table,
        "update_item",
        side_effect=ClientError(
            {"Error": {"Code": "ValidationException"}}, "UpdateItem"
        ),
    )

    # When
    with pytest.raises(ClientError) as exc_info:
        dynamodb_identity_wrapper.unset_system_trait(
            environment_api_key="api-key", identifier="user-1", trait_key="cohort_x"
        )

    # Then
    assert exc_info.value.response["Error"]["Code"] == "ValidationException"


def test_unset_system_trait__trait_absent__no_error(
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    dynamodb_identity_wrapper.put_item(
        {
            "composite_key": "api-key_user-1",
            "identifier": "user-1",
            "environment_api_key": "api-key",
            "system_traits": {"other": True},
        }
    )

    # When
    dynamodb_identity_wrapper.unset_system_trait(
        environment_api_key="api-key", identifier="user-1", trait_key="cohort_x"
    )

    # Then
    document = dynamodb_identity_wrapper.get_item("api-key_user-1")
    assert document is not None
    assert document["system_traits"] == {"other": True}
