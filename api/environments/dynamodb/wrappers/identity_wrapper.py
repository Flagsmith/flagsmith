import logging
import typing
from contextlib import suppress
from decimal import Decimal
from typing import Iterable

from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound

from edge_api.identities.search import EdgeIdentitySearchData
from environments.dynamodb.constants import (
    IDENTITIES_PAGINATION_LIMIT,
    SYSTEM_TRAIT_WRITE_MAX_ATTEMPTS,
)
from environments.dynamodb.wrappers.exceptions import (
    CapacityBudgetExceeded,
    SystemTraitWriteRaceError,
)
from util.engine_models.context.mappers import (
    is_context_in_segment,
    map_environment_identity_to_context,
)
from util.engine_models.identities.models import IdentityModel
from util.mappers import (
    map_engine_identity_to_identity_document,
    map_identity_to_identity_document,
)

from .base import BaseDynamoWrapper

if typing.TYPE_CHECKING:
    from boto3.dynamodb.conditions import ConditionBase
    from mypy_boto3_dynamodb.type_defs import (
        QueryInputRequestTypeDef,
        QueryOutputTableTypeDef,
        TableAttributeValueTypeDef,
    )

    from environments.identities.models import Identity

logger = logging.getLogger(__name__)


def _system_trait_value_matches(
    stored_value: object,
    document_value: bool | int | Decimal | str,
) -> bool:
    # The bool check stops `Decimal(1) == True` false positives.
    return (
        isinstance(stored_value, bool) == isinstance(document_value, bool)
        and stored_value == document_value
    )


class DynamoIdentityWrapper(BaseDynamoWrapper):
    def __init__(self) -> None:
        super().__init__()

    def get_table_name(self) -> str | None:  # type: ignore[override]
        return settings.IDENTITIES_TABLE_NAME_DYNAMO

    def query_items(self, *args, **kwargs) -> "QueryOutputTableTypeDef":  # type: ignore[no-untyped-def]
        return self.table.query(*args, **kwargs)  # type: ignore[union-attr]

    def put_item(self, identity_dict: dict):  # type: ignore[type-arg,no-untyped-def]
        self.table.put_item(Item=identity_dict)  # type: ignore[union-attr]

    def write_identities(self, identities: Iterable["Identity"]):  # type: ignore[no-untyped-def]
        with self.table.batch_writer() as batch:  # type: ignore[union-attr]
            for identity in identities:
                identity_document = map_identity_to_identity_document(identity)
                # Since sort keys can not be greater than 1024
                # https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html#limits-partition-sort-keys
                if len(identity_document["identifier"]) > 1024:  # type: ignore[arg-type]
                    logger.warning(
                        f"Can't migrate identity {identity.id}; identifier too long"
                    )
                    continue
                batch.put_item(Item=identity_document)

    def get_item(self, composite_key: str) -> typing.Optional[dict]:  # type: ignore[type-arg]
        return self.table.get_item(Key={"composite_key": composite_key}).get("Item")  # type: ignore[union-attr]

    def set_system_trait(
        self,
        *,
        environment_api_key: str,
        identifier: str,
        trait_key: str,
        trait_value: bool | int | float | str = True,
    ) -> None:
        """Idempotently set a system trait on an identity document.

        Writes only touch the `system_traits.<trait_key>` attribute, so
        concurrent writes to other attributes are never overwritten; the
        document is created if missing. Each write is conditional on the
        document shape just read — a lost race re-reads and retries, and
        `SystemTraitWriteRaceError` is raised once attempts are exhausted.

        Assumes stored documents never carry `system_traits` as NULL — the
        document mapper omits the attribute when unset.
        """
        composite_key = IdentityModel.generate_composite_key(
            environment_api_key, identifier
        )
        # DynamoDB rejects floats and returns all numbers as Decimal.
        document_value: bool | int | Decimal | str = (
            Decimal(str(trait_value)) if isinstance(trait_value, float) else trait_value
        )
        for _ in range(SYSTEM_TRAIT_WRITE_MAX_ATTEMPTS):
            # Strongly consistent read: a replication-lagged hint would burn
            # retry attempts on conditional writes that can never succeed.
            document = self.table.get_item(  # type: ignore[union-attr]
                Key={"composite_key": composite_key}, ConsistentRead=True
            ).get("Item")
            system_traits = document.get("system_traits") if document else None
            if isinstance(system_traits, dict) and _system_trait_value_matches(
                system_traits.get(trait_key), document_value
            ):
                return
            try:
                if document is None:
                    self.table.put_item(  # type: ignore[union-attr]
                        Item=map_engine_identity_to_identity_document(
                            IdentityModel(
                                identifier=identifier,
                                environment_api_key=environment_api_key,
                                system_traits={trait_key: trait_value},
                            )
                        ),
                        ConditionExpression="attribute_not_exists(composite_key)",
                    )
                elif isinstance(system_traits, dict):
                    self.table.update_item(  # type: ignore[union-attr]
                        Key={"composite_key": composite_key},
                        UpdateExpression="SET system_traits.#tk = :value",
                        ConditionExpression="attribute_exists(system_traits)",
                        ExpressionAttributeNames={"#tk": trait_key},
                        ExpressionAttributeValues={":value": document_value},
                    )
                else:
                    # If another writer created system_traits after we read
                    # the document, this write does nothing and their traits
                    # survive; the returned attributes tell us which happened.
                    response = self.table.update_item(  # type: ignore[union-attr]
                        Key={"composite_key": composite_key},
                        UpdateExpression=(
                            "SET system_traits = if_not_exists(system_traits, :init)"
                        ),
                        # Without this condition, update_item would re-create
                        # a just-deleted identity as an empty document
                        # containing nothing but this trait.
                        ConditionExpression="attribute_exists(composite_key)",
                        ExpressionAttributeValues={
                            ":init": {trait_key: document_value}
                        },
                        ReturnValues="ALL_NEW",
                    )
                    written_traits = response["Attributes"].get("system_traits")
                    if isinstance(written_traits, dict) and _system_trait_value_matches(
                        written_traits.get(trait_key), document_value
                    ):
                        return
                    continue
                return
            except ClientError as exc:
                if exc.response["Error"]["Code"] != "ConditionalCheckFailedException":
                    raise
        raise SystemTraitWriteRaceError(composite_key)

    def unset_system_trait(
        self,
        *,
        environment_api_key: str,
        identifier: str,
        trait_key: str,
    ) -> None:
        """Idempotently remove a system trait from an identity document."""
        composite_key = IdentityModel.generate_composite_key(
            environment_api_key, identifier
        )
        try:
            self.table.update_item(  # type: ignore[union-attr]
                Key={"composite_key": composite_key},
                UpdateExpression="REMOVE system_traits.#tk",
                # Failing this condition covers every no-op case at once:
                # missing document, missing system_traits, or trait already absent.
                ConditionExpression="attribute_exists(system_traits.#tk)",
                ExpressionAttributeNames={"#tk": trait_key},
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise

    def delete_item(self, composite_key: str):  # type: ignore[no-untyped-def]
        self.table.delete_item(Key={"composite_key": composite_key})  # type: ignore[union-attr]

    def delete_all_identities(self, environment_api_key: str):  # type: ignore[no-untyped-def]
        with self.table.batch_writer() as writer:  # type: ignore[union-attr]
            for item in self.iter_all_items_paginated(
                environment_api_key=environment_api_key,
                projection_expression="composite_key",
            ):
                writer.delete_item(Key={"composite_key": item["composite_key"]})

    def get_item_from_uuid(self, uuid: str) -> dict:  # type: ignore[type-arg]
        filter_expression = Key("identity_uuid").eq(uuid)
        query_kwargs = {
            "IndexName": "identity_uuid-index",
            "Limit": 1,
            "KeyConditionExpression": filter_expression,
        }
        try:
            return self.query_items(**query_kwargs)["Items"][0]
        except IndexError:
            raise ObjectDoesNotExist()

    def get_item_from_uuid_or_404(self, uuid: str) -> dict:  # type: ignore[type-arg]
        try:
            return self.get_item_from_uuid(uuid)
        except ObjectDoesNotExist as e:
            raise NotFound() from e

    def get_all_items(
        self,
        environment_api_key: str,
        limit: int,
        start_key: dict[str, "TableAttributeValueTypeDef"] | None = None,
        filter_expression: "ConditionBase | str | None" = None,
        projection_expression: str | None = None,
        return_consumed_capacity: bool = False,
    ) -> "QueryOutputTableTypeDef":
        key_condition_expression = Key("environment_api_key").eq(environment_api_key)
        query_kwargs: "QueryInputRequestTypeDef" = {  # type: ignore[typeddict-item]
            "IndexName": "environment_api_key-identifier-index",
            "KeyConditionExpression": key_condition_expression,  # type: ignore[typeddict-item]
            "Limit": limit,
        }
        if start_key:
            query_kwargs["ExclusiveStartKey"] = start_key
        if filter_expression:
            query_kwargs["FilterExpression"] = filter_expression  # type: ignore[typeddict-item]
        if projection_expression:
            query_kwargs["ProjectionExpression"] = projection_expression
        if return_consumed_capacity:
            # Use `TOTAL` because we don't need per-index/per-table consumed capacity
            query_kwargs["ReturnConsumedCapacity"] = "TOTAL"
        return self.query_items(**query_kwargs)

    def iter_all_items_paginated(
        self,
        environment_api_key: str,
        limit: int = IDENTITIES_PAGINATION_LIMIT,
        projection_expression: str | None = None,
        capacity_budget: Decimal = Decimal("Inf"),
        overrides_only: bool = False,
    ) -> typing.Generator[dict, None, None]:  # type: ignore[type-arg]
        last_evaluated_key = "initial"
        get_all_items_kwargs = {
            "environment_api_key": environment_api_key,
            "limit": limit,
            "projection_expression": projection_expression,
            "return_consumed_capacity": capacity_budget != Decimal("Inf"),
        }
        if overrides_only:
            get_all_items_kwargs["filter_expression"] = Attr("identity_features").ne([])
        capacity_spent = 0
        while last_evaluated_key:
            if capacity_spent >= capacity_budget:
                raise CapacityBudgetExceeded(
                    capacity_budget=capacity_budget,
                    capacity_spent=capacity_spent,  # type: ignore[arg-type]
                )
            query_response = self.get_all_items(
                **get_all_items_kwargs,  # type: ignore[arg-type]
            )
            with suppress(KeyError):
                capacity_spent += query_response["ConsumedCapacity"]["CapacityUnits"]  # type: ignore[assignment]
            for item in query_response["Items"]:
                yield item
            if last_evaluated_key := query_response.get("LastEvaluatedKey"):  # type: ignore[assignment]
                get_all_items_kwargs["start_key"] = last_evaluated_key

    def search_items(
        self,
        environment_api_key: str,
        search_data: EdgeIdentitySearchData,
        limit: int,
        start_key: dict = None,  # type: ignore[type-arg,assignment]
    ) -> "QueryOutputTableTypeDef":
        partition_key_search_expression = Key("environment_api_key").eq(
            environment_api_key
        )
        sort_key_search_expression = getattr(
            Key(search_data.search_attribute), search_data.dynamo_search_method
        )(search_data.search_term)

        query_kwargs = {
            "IndexName": search_data.dynamo_index_name,
            "Limit": limit,
            "KeyConditionExpression": partition_key_search_expression
            & sort_key_search_expression,
        }
        if start_key:
            query_kwargs.update(ExclusiveStartKey=start_key)

        return self.query_items(**query_kwargs)

    def get_segment_ids(
        self,
        identity_pk: str = None,  # type: ignore[assignment]
        identity_model: IdentityModel = None,  # type: ignore[assignment]
    ) -> list:  # type: ignore[type-arg]
        from environments.models import Environment
        from util.mappers.engine import map_segment_to_engine

        if not (identity_pk or identity_model):
            raise ValueError("Must provide one of identity_pk or identity_model.")

        with suppress(ObjectDoesNotExist):
            identity = identity_model or IdentityModel.model_validate(
                self.get_item_from_uuid(identity_pk)
            )
            environment = Environment.objects.select_related("project").get(
                api_key=identity.environment_api_key,
            )
            segments = environment.project.get_segments_from_cache()
            context = map_environment_identity_to_context(
                environment=environment,
                identity=identity,
                override_traits=None,
            )
            return [
                segment.id
                for segment in segments
                if is_context_in_segment(context, map_segment_to_engine(segment))
            ]

        return []
