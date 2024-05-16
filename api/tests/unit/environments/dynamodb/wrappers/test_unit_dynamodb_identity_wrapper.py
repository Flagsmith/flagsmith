import typing
from decimal import Decimal

import pytest
from boto3.dynamodb.conditions import Key
from core.constants import INTEGER
from django.core.exceptions import ObjectDoesNotExist
from flag_engine.identities.models import IdentityModel
from flag_engine.segments.constants import IN
from mypy_boto3_dynamodb.service_resource import Table
from pytest_mock import MockerFixture
from rest_framework.exceptions import NotFound

from environments.dynamodb import DynamoIdentityWrapper
from environments.dynamodb.wrappers.exceptions import CapacityBudgetExceeded
from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from segments.models import Condition, Segment, SegmentRule
from util.mappers import (
    map_environment_to_environment_document,
    map_identity_to_identity_document,
)

if typing.TYPE_CHECKING:
    from environments.models import Environment
    from projects.models import Project


def test_get_item_from_uuid_calls_query_with_correct_argument(mocker):
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


def test_get_item_from_uuid_raises_object_does_not_exists_if_identity_is_not_returned(
    mocker,
):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")
    mocked_dynamo_table.query.return_value = {"Items": [], "Count": 0}
    # Then
    with pytest.raises(ObjectDoesNotExist):
        dynamo_identity_wrapper.get_item_from_uuid("identity_uuid")


def test_get_item_from_uuid_or_404_calls_get_item_from_uuid_with_correct_arguments(
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


def test_get_item_from_uuid_or_404_calls_raises_not_found_if_internal_method_raises_object_does_not_exists(
    mocker,
):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    mocker.patch.object(
        dynamo_identity_wrapper, "get_item_from_uuid", side_effect=ObjectDoesNotExist
    )
    identity_uuid = "test_uuid"

    # Then
    with pytest.raises(NotFound):
        dynamo_identity_wrapper.get_item_from_uuid_or_404(identity_uuid)


def test_delete_item_calls_dynamo_delete_item_with_correct_arguments(mocker):
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


def test_get_item_calls_dynamo_get_item_with_correct_arguments(mocker):
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


def test_get_all_items_without_start_key_calls_query_with_correct_arguments(mocker):
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


def test_get_all_items_with_start_key_calls_query_with_correct_arguments(mocker):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()

    environment_key = "environment_key"
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")
    start_key = {"key": "value"}

    # When
    dynamo_identity_wrapper.get_all_items(environment_key, 999, start_key)

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


def test_search_items_with_identifier_calls_query_with_correct_arguments(mocker):
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    environment_key = "environment_key"
    identifier = "test_user"
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")
    start_key = {"key": "value"}
    search_function = lambda x: Key("identifier").eq(x)  # noqa: E731

    # When
    dynamo_identity_wrapper.search_items_with_identifier(
        environment_key, identifier, search_function, 999, start_key
    )

    # Then
    mocked_dynamo_table.query.assert_called_with(
        IndexName="environment_api_key-identifier-index",
        Limit=999,
        KeyConditionExpression=Key("environment_api_key").eq(environment_key)
        & search_function(identifier),
        ExclusiveStartKey=start_key,
    )


def test_write_identities_calls_internal_methods_with_correct_arguments(
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


def test_write_identities_skips_identity_if_identifier_is_too_large(
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


def test_is_enabled_is_false_if_dynamo_table_name_is_not_set(settings, mocker):
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


def test_is_enabled_is_true_if_dynamo_table_name_is_set(settings, mocker):
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


def test_get_segment_ids_returns_correct_segment_ids(
    project, environment, identity, identity_matching_segment, mocker
):
    # Given - two segments (one that matches the identity and one that does not)
    Segment.objects.create(name="Non matching segment", project=project)

    identity_document = map_identity_to_identity_document(identity)
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    mocked_get_item_from_uuid = mocker.patch.object(
        dynamo_identity_wrapper, "get_item_from_uuid", return_value=identity_document
    )
    identity_uuid = identity_document["identity_uuid"]

    environment_document = map_environment_to_environment_document(environment)
    mocked_environment_wrapper = mocker.patch(
        "environments.dynamodb.wrappers.identity_wrapper.DynamoEnvironmentWrapper"
    )
    mocked_environment_wrapper.return_value.get_item.return_value = environment_document

    # When
    segment_ids = dynamo_identity_wrapper.get_segment_ids(identity_uuid)

    # Then
    assert segment_ids == [identity_matching_segment.id]
    mocked_get_item_from_uuid.assert_called_with(identity_uuid)
    mocked_environment_wrapper.return_value.get_item.assert_called_with(
        environment.api_key
    )


def test_get_segment_ids_returns_segment_using_in_operator_for_integer_traits(
    project: "Project", environment: "Environment", mocker: "MockerFixture"
) -> None:
    """
    Specific test to cover https://github.com/Flagsmith/flagsmith/issues/2602
    """
    # Given
    trait_key = "trait_key"

    segment = Segment.objects.create(name="Test Segment", project=project)
    parent_rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    child_rule = SegmentRule.objects.create(rule=parent_rule, type=SegmentRule.ANY_RULE)
    Condition.objects.create(
        property=trait_key, operator=IN, value="1,2,3,4", rule=child_rule
    )

    identity = Identity.objects.create(environment=environment, identifier="identifier")
    Trait.objects.create(
        trait_key=trait_key, integer_value=1, value_type=INTEGER, identity=identity
    )

    identity_document = map_identity_to_identity_document(identity)
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    mocker.patch.object(
        dynamo_identity_wrapper, "get_item_from_uuid", return_value=identity_document
    )
    identity_uuid = identity_document["identity_uuid"]

    environment_document = map_environment_to_environment_document(environment)
    mocked_environment_wrapper = mocker.patch(
        "environments.dynamodb.wrappers.identity_wrapper.DynamoEnvironmentWrapper"
    )
    mocked_environment_wrapper.return_value.get_item.return_value = environment_document

    # When
    segment_ids = dynamo_identity_wrapper.get_segment_ids(identity_uuid)

    # Then
    assert segment_ids == [segment.id]


def test_get_segment_ids_returns_empty_list_if_identity_does_not_exists(
    project, environment, identity, mocker
):
    # Given
    identity_document = map_identity_to_identity_document(identity)
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    mocker.patch.object(
        dynamo_identity_wrapper, "get_item_from_uuid", side_effect=ObjectDoesNotExist
    )
    identity_uuid = identity_document["identity_uuid"]

    # Then
    segment_ids = dynamo_identity_wrapper.get_segment_ids(identity_uuid)

    # Then
    assert segment_ids == []


def test_get_segment_ids_throws_value_error_if_no_arguments():
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()

    # When
    with pytest.raises(ValueError):
        dynamo_identity_wrapper.get_segment_ids()

    # Then
    # exception raised


def test_get_segment_ids_throws_value_error_if_arguments_not_valid():
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()

    # When
    with pytest.raises(ValueError):
        dynamo_identity_wrapper.get_segment_ids(None)

    # Then
    # exception raised


def test_get_segment_ids_with_identity_model(identity, environment, mocker):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    identity_document = map_identity_to_identity_document(identity)
    identity_model = IdentityModel.parse_obj(identity_document)

    mocker.patch.object(
        dynamo_identity_wrapper, "get_item_from_uuid", return_value=identity_document
    )

    environment_document = map_environment_to_environment_document(environment)
    mocked_environment_wrapper = mocker.patch(
        "environments.dynamodb.wrappers.identity_wrapper.DynamoEnvironmentWrapper"
    )
    mocked_environment_wrapper.return_value.get_item.return_value = environment_document

    # When
    segment_ids = dynamo_identity_wrapper.get_segment_ids(identity_model=identity_model)

    # Then
    assert segment_ids == []


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
def test_identity_wrapper__iter_all_items_paginated__capacity_budget_set__raises_expected(
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


def test_delete_all_identities__deletes_all_identities_documents_from_dynamodb(
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
