import logging
import typing
from typing import Mapping

import boto3
from amazondax import AmazonDaxClient
from botocore.config import Config
from django.conf import settings

if typing.TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import (
        DeleteItemOutputTableTypeDef,
        GetItemOutputTableTypeDef,
        Table,
        TableAttributeValueTypeDef,
    )


logger = logging.getLogger()


class BaseDynamoWrapper:
    table_name: str = None

    def __init__(self) -> None:
        self._table: typing.Optional["Table"] = None

    @property
    def table(self) -> typing.Optional["Table"]:
        if not self._table:
            self._table = self.get_table()
        return self._table

    def get_table_name(self) -> str:
        return self.table_name

    def get_table(self) -> typing.Optional["Table"]:
        if table_name := self.get_table_name():
            return boto3.resource("dynamodb", config=Config(tcp_keepalive=True)).Table(
                table_name
            )

    def get_item(
        self, key: Mapping[str, "TableAttributeValueTypeDef"]
    ) -> "GetItemOutputTableTypeDef":
        return self.table.get_item(Key=key)

    def delete_item(
        self, key: Mapping[str, "TableAttributeValueTypeDef"]
    ) -> "DeleteItemOutputTableTypeDef":
        return self.table.delete_item(Key=key)

    @property
    def is_enabled(self) -> bool:
        return self.table is not None

    def query_get_all_items(self, **kwargs: dict) -> typing.Generator[dict, None, None]:
        while True:
            query_response = self.table.query(**kwargs)
            for item in query_response["Items"]:
                yield item

            last_evaluated_key = query_response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break

            kwargs["ExclusiveStartKey"] = last_evaluated_key

    def batch_write(self, items: list) -> None:
        with self.table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)


class DAXWrapper(BaseDynamoWrapper):
    def __init__(self) -> None:
        super().__init__()
        self._dax_table: typing.Optional["Table"] = None

    @property
    def dax_table(self):
        if not self._dax_table and settings.DAX_ENDPOINT:
            self._dax_table = AmazonDaxClient.resource(
                endpoint_url=settings.DAX_ENDPOINT, config=Config(tcp_keepalive=True)
            ).Table(self.table_name)

        return self._dax_table

    def get_item(
        self, key: Mapping[str, "TableAttributeValueTypeDef"]
    ) -> "GetItemOutputTableTypeDef":
        try:
            return self.dax_table.get_item(Key=key)
        except Exception as e:
            logger.error("Error getting item from DAX: %s", e)
            return super().get_item(key)

    def delete_item(
        self, key: Mapping[str, "TableAttributeValueTypeDef"]
    ) -> "DeleteItemOutputTableTypeDef":
        try:
            return self.dax_table.delete_item(Key=key)
        except Exception as e:
            logger.error("Error deleting item from DAX: %s", e)
            return super().delete_item(key)

    def batch_write(self, items: list):
        try:
            with self._dax_table.batch_writer() as batch:
                for item in items:
                    batch.put_item(Item=item)
        except Exception as e:
            logger.error("Error batch writing item from DAX: %s", e)
            super().batch_write(items)
