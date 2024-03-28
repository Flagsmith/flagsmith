import logging
import typing
from contextlib import suppress
from typing import Iterable

from boto3.dynamodb.conditions import Key
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from flag_engine.environments.models import EnvironmentModel
from flag_engine.identities.models import IdentityModel
from flag_engine.segments.evaluator import get_identity_segments
from rest_framework.exceptions import NotFound

from environments.dynamodb.constants import IDENTITIES_PAGINATION_LIMIT
from util.mappers import map_identity_to_identity_document

from .base import BaseDynamoWrapper
from .environment_wrapper import DynamoEnvironmentWrapper

if typing.TYPE_CHECKING:
    from mypy_boto3_dynamodb.type_defs import (
        QueryInputRequestTypeDef,
        QueryOutputTableTypeDef,
        TableAttributeValueTypeDef,
    )

    from environments.identities.models import Identity

logger = logging.getLogger()


class DynamoIdentityWrapper(BaseDynamoWrapper):
    def get_table_name(self) -> str | None:
        return settings.IDENTITIES_TABLE_NAME_DYNAMO

    def query_items(self, *args, **kwargs) -> "QueryOutputTableTypeDef":
        return self.table.query(*args, **kwargs)

    def put_item(self, identity_dict: dict):
        self.table.put_item(Item=identity_dict)

    def write_identities(self, identities: Iterable["Identity"]):
        with self.table.batch_writer() as batch:
            for identity in identities:
                identity_document = map_identity_to_identity_document(identity)
                # Since sort keys can not be greater than 1024
                # https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html#limits-partition-sort-keys
                if len(identity_document["identifier"]) > 1024:
                    logger.warning(
                        f"Can't migrate identity {identity.id}; identifier too long"
                    )
                    continue
                batch.put_item(Item=identity_document)

    def get_item(self, composite_key: str) -> typing.Optional[dict]:
        return self.table.get_item(Key={"composite_key": composite_key}).get("Item")

    def delete_item(self, composite_key: str):
        self.table.delete_item(Key={"composite_key": composite_key})

    def delete_all_identities(self, environment_api_key: str):
        with self.table.batch_writer() as writer:
            for item in self.iter_all_items_paginated(
                environment_api_key=environment_api_key,
                projection_expression="composite_key",
            ):
                writer.delete_item(Key={"composite_key": item["composite_key"]})

    def get_item_from_uuid(self, uuid: str) -> dict:
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

    def get_item_from_uuid_or_404(self, uuid: str) -> dict:
        try:
            return self.get_item_from_uuid(uuid)
        except ObjectDoesNotExist as e:
            raise NotFound() from e

    def get_all_items(
        self,
        environment_api_key: str,
        limit: int,
        start_key: dict[str, "TableAttributeValueTypeDef"] | None = None,
        projection_expression: str = None,
    ) -> "QueryOutputTableTypeDef":
        filter_expression = Key("environment_api_key").eq(environment_api_key)
        query_kwargs: "QueryInputRequestTypeDef" = {
            "IndexName": "environment_api_key-identifier-index",
            "KeyConditionExpression": filter_expression,
            "Limit": limit,
        }
        if projection_expression:
            query_kwargs["ProjectionExpression"] = projection_expression

        if start_key:
            query_kwargs["ExclusiveStartKey"] = start_key
        return self.query_items(**query_kwargs)

    def iter_all_items_paginated(
        self,
        environment_api_key: str,
        limit: int = IDENTITIES_PAGINATION_LIMIT,
        projection_expression: str = None,
    ) -> typing.Generator[dict, None, None]:
        last_evaluated_key = "initial"
        get_all_items_kwargs = {
            "environment_api_key": environment_api_key,
            "limit": limit,
            "projection_expression": projection_expression,
        }
        while last_evaluated_key:
            query_response = self.get_all_items(
                **get_all_items_kwargs,
            )
            for item in query_response["Items"]:
                yield item
            if last_evaluated_key := query_response.get("LastEvaluatedKey"):
                get_all_items_kwargs["start_key"] = last_evaluated_key

    def search_items_with_identifier(
        self,
        environment_api_key: str,
        identifier: str,
        search_function: typing.Callable,
        limit: int,
        start_key: dict = None,
    ):
        filter_expression = Key("environment_api_key").eq(
            environment_api_key
        ) & search_function(identifier)
        query_kwargs = {
            "IndexName": "environment_api_key-identifier-index",
            "Limit": limit,
            "KeyConditionExpression": filter_expression,
        }
        if start_key:
            query_kwargs.update(ExclusiveStartKey=start_key)
        return self.query_items(**query_kwargs)

    def get_segment_ids(
        self, identity_pk: str = None, identity_model: IdentityModel = None
    ) -> list:
        if not (identity_pk or identity_model):
            raise ValueError("Must provide one of identity_pk or identity_model.")

        with suppress(ObjectDoesNotExist):
            identity = identity_model or IdentityModel.model_validate(
                self.get_item_from_uuid(identity_pk)
            )
            environment_wrapper = DynamoEnvironmentWrapper()
            environment = EnvironmentModel.model_validate(
                environment_wrapper.get_item(identity.environment_api_key)
            )
            segments = get_identity_segments(environment, identity)
            return [segment.id for segment in segments]

        return []
