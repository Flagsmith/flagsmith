import typing
from typing import Any, Iterable

from boto3.dynamodb.conditions import Key
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from environments.dynamodb.constants import (
    DYNAMODB_MAX_BATCH_WRITE_ITEM_COUNT,
    ENVIRONMENTS_V2_PARTITION_KEY,
    ENVIRONMENTS_V2_SORT_KEY,
)
from environments.dynamodb.types import IdentityOverridesV2Changeset
from environments.dynamodb.utils import (
    get_environments_v2_identity_override_document_key,
)
from util.mappers import (
    map_environment_to_environment_document,
    map_environment_to_environment_v2_document,
    map_identity_override_to_identity_override_document,
)
from util.util import iter_paired_chunks

from .base import BaseDynamoWrapper

if typing.TYPE_CHECKING:
    from mypy_boto3_dynamodb.type_defs import QueryInputRequestTypeDef

    from environments.models import Environment


class BaseDynamoEnvironmentWrapper(BaseDynamoWrapper):
    def write_environment(self, environment: "Environment") -> None:
        self.write_environments([environment])

    def write_environments(self, environments: Iterable["Environment"]) -> None:
        raise NotImplementedError()


class DynamoEnvironmentWrapper(BaseDynamoEnvironmentWrapper):
    def get_table_name(self) -> str | None:
        return settings.ENVIRONMENTS_TABLE_NAME_DYNAMO

    def write_environments(self, environments: Iterable["Environment"]):
        with self.table.batch_writer() as writer:
            for environment in environments:
                writer.put_item(
                    Item=map_environment_to_environment_document(environment),
                )

    def get_item(self, api_key: str) -> dict:
        try:
            return self.table.get_item(Key={"api_key": api_key})["Item"]
        except KeyError as e:
            raise ObjectDoesNotExist() from e

    def delete_environment(self, api_key: str) -> None:
        self.table.delete_item(Key={"api_key": api_key})


class DynamoEnvironmentV2Wrapper(BaseDynamoEnvironmentWrapper):
    def get_table_name(self) -> str | None:
        return settings.ENVIRONMENTS_V2_TABLE_NAME_DYNAMO

    def get_identity_overrides_by_environment_id(
        self,
        environment_id: int,
        feature_id: int | None = None,
    ) -> typing.List[dict[str, Any]]:
        try:
            return list(
                self.query_get_all_items(
                    KeyConditionExpression=Key(ENVIRONMENTS_V2_PARTITION_KEY).eq(
                        str(environment_id),
                    )
                    & Key(ENVIRONMENTS_V2_SORT_KEY).begins_with(
                        get_environments_v2_identity_override_document_key(
                            feature_id=feature_id,
                        ),
                    )
                )
            )
        except KeyError as e:
            raise ObjectDoesNotExist() from e

    def update_identity_overrides(
        self,
        changeset: IdentityOverridesV2Changeset,
    ) -> None:
        for to_put, to_delete in iter_paired_chunks(
            changeset.to_put,
            changeset.to_delete,
            chunk_size=DYNAMODB_MAX_BATCH_WRITE_ITEM_COUNT,
        ):
            with self.table.batch_writer() as writer:
                for identity_override_to_delete in to_delete:
                    writer.delete_item(
                        Key={
                            ENVIRONMENTS_V2_PARTITION_KEY: identity_override_to_delete.environment_id,
                            ENVIRONMENTS_V2_SORT_KEY: identity_override_to_delete.document_key,
                        },
                    )
                for identity_override_to_put in to_put:
                    writer.put_item(
                        Item=map_identity_override_to_identity_override_document(
                            identity_override_to_put
                        ),
                    )

    def write_environments(self, environments: Iterable["Environment"]) -> None:
        with self.table.batch_writer() as writer:
            for environment in environments:
                writer.put_item(
                    Item=map_environment_to_environment_v2_document(environment),
                )

    def delete_environment(self, environment_id: int):
        environment_id = str(environment_id)
        filter_expression = Key(ENVIRONMENTS_V2_PARTITION_KEY).eq(environment_id)
        query_kwargs: "QueryInputRequestTypeDef" = {
            "KeyConditionExpression": filter_expression,
            "ProjectionExpression": "document_key",
        }
        with self.table.batch_writer() as writer:
            for item in self.query_get_all_items(**query_kwargs):
                writer.delete_item(
                    Key={
                        ENVIRONMENTS_V2_PARTITION_KEY: environment_id,
                        ENVIRONMENTS_V2_SORT_KEY: item["document_key"],
                    },
                )
