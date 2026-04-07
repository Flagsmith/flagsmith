import abc
import typing
from typing import Any, Iterable

import structlog
from boto3.dynamodb.conditions import Key
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import prefetch_related_objects

from environments.dynamodb.constants import (
    DYNAMODB_MAX_BATCH_WRITE_ITEM_COUNT,
    ENVIRONMENTS_V2_PARTITION_KEY,
    ENVIRONMENTS_V2_SORT_KEY,
)
from environments.dynamodb.types import IdentityOverridesV2Changeset
from environments.dynamodb.utils import (
    estimate_document_size,
    get_environments_v2_identity_override_document_key,
)
from environments.metrics import (
    flagsmith_dynamo_environment_document_compression_ratio,
    flagsmith_dynamo_environment_document_size_bytes,
)
from integrations.flagsmith.client import get_openfeature_client
from util.mappers import (
    map_environment_to_compressed_environment_document,
    map_environment_to_compressed_environment_v2_document,
    map_environment_to_environment_document,
    map_environment_to_environment_v2_document,
    map_identity_override_to_identity_override_document,
)
from util.util import iter_paired_chunks

from .base import BaseDynamoWrapper

if typing.TYPE_CHECKING:
    from mypy_boto3_dynamodb.type_defs import QueryInputRequestTypeDef

    from environments.models import Environment
    from util.dataclasses import CompressedEnvironmentDocument

logger = structlog.get_logger("dynamodb")


class BaseDynamoEnvironmentWrapper(BaseDynamoWrapper, abc.ABC):
    def write_environment(self, environment: "Environment") -> None:
        self.write_environments([environment])

    def write_environments(self, environments: Iterable["Environment"]) -> None:
        self._write_environments(environments)

    @abc.abstractmethod
    def _map_environment_document(
        self,
        environment: "Environment",
    ) -> dict[str, Any]: ...

    @abc.abstractmethod
    def _map_compressed_environment_document(
        self,
        environment: "Environment",
    ) -> "CompressedEnvironmentDocument": ...

    def _write_environments(self, environments: Iterable["Environment"]) -> None:
        openfeature_client = get_openfeature_client()
        prefetch_related_objects(
            environments,
            "project__organisation",
            "project__organisation__subscription",
        )

        assert self.table
        with self.table.batch_writer() as writer:
            for environment in environments:
                organisation = environment.project.organisation
                if openfeature_client.get_boolean_value(
                    "compress_dynamo_documents",
                    default_value=False,
                    evaluation_context=organisation.openfeature_evaluation_context,
                ):
                    result = self._map_compressed_environment_document(environment)
                    writer.put_item(Item=result.document)

                    flagsmith_dynamo_environment_document_size_bytes.labels(
                        table=self.get_table_name(),
                        compressed="true",
                    ).observe(result.compressed_size_bytes)
                    flagsmith_dynamo_environment_document_compression_ratio.labels(
                        table=self.get_table_name(),
                    ).observe(result.compression_ratio)
                    logger.info(
                        "environment-document-compressed",
                        environment_id=environment.id,
                        environment_api_key=environment.api_key,
                    )
                else:
                    item = self._map_environment_document(environment)
                    writer.put_item(Item=item)

                    flagsmith_dynamo_environment_document_size_bytes.labels(
                        table=self.get_table_name(),
                        compressed="false",
                    ).observe(estimate_document_size(item))


class DynamoEnvironmentWrapper(BaseDynamoEnvironmentWrapper):
    def get_table_name(self) -> str | None:  # type: ignore[override]
        return settings.ENVIRONMENTS_TABLE_NAME_DYNAMO

    def _map_environment_document(self, environment: "Environment") -> dict[str, Any]:
        return map_environment_to_environment_document(environment)

    def _map_compressed_environment_document(
        self, environment: "Environment"
    ) -> "CompressedEnvironmentDocument":
        return map_environment_to_compressed_environment_document(environment)

    def get_item(self, api_key: str) -> dict:  # type: ignore[type-arg]
        try:
            return self.table.get_item(Key={"api_key": api_key})["Item"]  # type: ignore[union-attr]
        except KeyError as e:
            raise ObjectDoesNotExist() from e

    def delete_environment(self, api_key: str) -> None:
        self.table.delete_item(Key={"api_key": api_key})  # type: ignore[union-attr]


class DynamoEnvironmentV2Wrapper(BaseDynamoEnvironmentWrapper):
    def get_table_name(self) -> str:
        return settings.ENVIRONMENTS_V2_TABLE_NAME_DYNAMO

    def get_identity_overrides_by_environment_id(
        self,
        environment_id: int,
        feature_id: int | None = None,
        projection_expression_attributes: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        key_condition_expression = self.get_identity_overrides_key_condition_expression(
            environment_id=environment_id,
            feature_id=feature_id,
        )
        query_kwargs: dict[str, Any] = {
            "KeyConditionExpression": key_condition_expression,
        }
        if projection_expression_attributes:
            query_kwargs["ProjectionExpression"] = ",".join(
                projection_expression_attributes
            )

        try:
            return list(self.query_iter_all_items(**query_kwargs))
        except KeyError as e:
            raise ObjectDoesNotExist() from e

    def get_identity_overrides_key_condition_expression(
        self,
        environment_id: int,
        feature_id: None | int,
    ) -> Key:
        return Key(ENVIRONMENTS_V2_PARTITION_KEY).eq(  # type: ignore[return-value]
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
            with self.table.batch_writer() as writer:  # type: ignore[union-attr]
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

    def _map_environment_document(self, environment: "Environment") -> dict[str, Any]:
        return map_environment_to_environment_v2_document(environment)

    def _map_compressed_environment_document(
        self,
        environment: "Environment",
    ) -> "CompressedEnvironmentDocument":
        return map_environment_to_compressed_environment_v2_document(environment)

    def delete_environment(self, environment_id: int):  # type: ignore[no-untyped-def]
        environment_id = str(environment_id)  # type: ignore[assignment]
        filter_expression = Key(ENVIRONMENTS_V2_PARTITION_KEY).eq(environment_id)
        query_kwargs: "QueryInputRequestTypeDef" = {  # type: ignore[typeddict-item]
            "KeyConditionExpression": filter_expression,  # type: ignore[typeddict-item]
            "ProjectionExpression": "document_key",
        }
        with self.table.batch_writer() as writer:  # type: ignore[union-attr]
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
        query_kwargs: "QueryInputRequestTypeDef" = {  # type: ignore[typeddict-item]
            "KeyConditionExpression": filter_expression,  # type: ignore[typeddict-item]
            "ProjectionExpression": "document_key",
        }

        with self.table.batch_writer() as writer:  # type: ignore[union-attr]
            for item in self.query_iter_all_items(**query_kwargs):
                writer.delete_item(
                    Key={
                        ENVIRONMENTS_V2_PARTITION_KEY: str(environment_id),
                        ENVIRONMENTS_V2_SORT_KEY: item["document_key"],
                    }
                )
