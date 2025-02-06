import typing
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
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


@dataclass
class IdentityOverridesQueryResponse:
    items: list[dict[str, Any]]
    is_num_identity_overrides_complete: bool


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
        feature_ids: None | list[int] = None,
    ) -> list[dict[str, Any]] | list[IdentityOverridesQueryResponse]:

        try:
            if feature_ids is None:
                return list(
                    self.query_iter_all_items(
                        KeyConditionExpression=self.get_identity_overrides_key_condition_expression(
                            environment_id=environment_id,
                            feature_id=feature_id,
                        )
                    )
                )

            else:
                futures = []
                with ThreadPoolExecutor() as executor:
                    for feature_id in feature_ids:
                        futures.append(
                            executor.submit(
                                self.get_identity_overrides_page,
                                environment_id,
                                feature_id,
                            )
                        )

                results = [future.result() for future in futures]
                return results

        except KeyError as e:
            raise ObjectDoesNotExist() from e

    def get_identity_overrides_page(
        self, environment_id: int, feature_id: int
    ) -> IdentityOverridesQueryResponse:
        query_response = self.table.query(
            KeyConditionExpression=self.get_identity_overrides_key_condition_expression(
                environment_id=environment_id,
                feature_id=feature_id,
            )
        )
        last_evaluated_key = query_response.get("LastEvaluatedKey")
        return IdentityOverridesQueryResponse(
            items=query_response["Items"],
            is_num_identity_overrides_complete=last_evaluated_key is None,
        )

    def get_identity_overrides_key_condition_expression(
        self,
        environment_id: int,
        feature_id: None | int,
    ) -> Key:
        return Key(ENVIRONMENTS_V2_PARTITION_KEY).eq(
            str(environment_id),
        ) & Key(ENVIRONMENTS_V2_SORT_KEY).begins_with(
            get_environments_v2_identity_override_document_key(
                feature_id=feature_id,
            ),
        )

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
            for item in self.query_iter_all_items(**query_kwargs):
                writer.delete_item(
                    Key={
                        ENVIRONMENTS_V2_PARTITION_KEY: environment_id,
                        ENVIRONMENTS_V2_SORT_KEY: item["document_key"],
                    },
                )

    def delete_identity_overrides(self, environment_id: int, feature_id: int) -> None:
        filter_expression = self.get_identity_overrides_key_condition_expression(
            environment_id=environment_id, feature_id=feature_id
        )
        query_kwargs: "QueryInputRequestTypeDef" = {
            "KeyConditionExpression": filter_expression,
            "ProjectionExpression": "document_key",
        }

        for item in self.query_iter_all_items(**query_kwargs):
            self.table.delete_item(
                Key={
                    ENVIRONMENTS_V2_PARTITION_KEY: str(environment_id),
                    ENVIRONMENTS_V2_SORT_KEY: item["document_key"],
                }
            )
