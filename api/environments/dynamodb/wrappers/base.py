import typing
from decimal import Context
from functools import partial

import boto3
import boto3.dynamodb.types
import structlog
from botocore.config import Config
from sentry_sdk import set_context

if typing.TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table
    from mypy_boto3_dynamodb.type_defs import (
        QueryOutputTableTypeDef,
        ScanOutputTableTypeDef,
        TableAttributeValueTypeDef,
    )

    DynamoDBOutput = QueryOutputTableTypeDef | ScanOutputTableTypeDef

    P = typing.ParamSpec("P")

# Avoid `decimal.Rounded` when reading large numbers
# See https://github.com/boto/boto3/issues/2500
boto3.dynamodb.types.DYNAMODB_CONTEXT = Context(prec=100)


logger: structlog.BoundLogger = structlog.get_logger()


class BaseDynamoWrapper:
    table_name: str = None

    def __init__(self) -> None:
        self._table: typing.Optional["Table"] = None
        self._log = logger.bind(table_name=self.table_name)

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

    def _iter_all_items(
        self,
        response_getter_method: "typing.Callable[[P], DynamoDBOutput]",
        **kwargs: "P.kwargs",
    ) -> typing.Generator[dict[str, "TableAttributeValueTypeDef"], None, None]:
        response_getter = partial(response_getter_method, **kwargs)
        set_context(
            "dynamodb",
            {"table_name": self.table_name, **kwargs},
        )

        while True:
            query_response = response_getter()

            for item in query_response["Items"]:
                yield item

            last_evaluated_key = query_response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break

            response_getter.keywords["ExclusiveStartKey"] = last_evaluated_key
            set_context(
                "dynamodb",
                {"table_name": self.table_name, **response_getter.keywords},
            )

    def scan_iter_all_items(
        self,
        **kwargs: typing.Any,
    ) -> typing.Generator[dict[str, "TableAttributeValueTypeDef"], None, None]:
        return self._iter_all_items(self.table.scan, **kwargs)

    def query_iter_all_items(
        self,
        **kwargs: typing.Any,
    ) -> typing.Generator[dict[str, "TableAttributeValueTypeDef"], None, None]:
        return self._iter_all_items(self.table.query, **kwargs)
