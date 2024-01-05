import typing

import boto3
from botocore.config import Config

if typing.TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table


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
