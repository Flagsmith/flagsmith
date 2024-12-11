import typing
from decimal import Context
from functools import partial

import boto3
import boto3.dynamodb.types
from botocore.config import Config

if typing.TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table


# Avoid `decimal.Rounded` when reading large numbers
# See https://github.com/boto/boto3/issues/2500
boto3.dynamodb.types.DYNAMODB_CONTEXT = Context(prec=100)


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
        if kwargs:
            response_getter = partial(self.table.query, **kwargs)
        else:
            response_getter = partial(self.table.scan)

        while True:
            query_response = response_getter()
            for item in query_response["Items"]:
                yield item

            last_evaluated_key = query_response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break

            response_getter.keywords["ExclusiveStartKey"] = last_evaluated_key
