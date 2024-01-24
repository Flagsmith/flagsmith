import typing

import boto3
from amazondax import AmazonDaxClient
from botocore.config import Config
from django.conf import settings

if typing.TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table


def get_dynamo_table(table_name) -> "Table":
    if settings.DAX_ENDPOINT:
        return AmazonDaxClient.resource(
            endpoint_url=settings.DAX_ENDPOINT, config=Config(tcp_keepalive=True)
        ).Table(table_name)

    return boto3.resource("dynamodb", config=Config(tcp_keepalive=True)).Table(
        table_name
    )
