import typing

from django.conf import settings

from util.mappers import (
    map_environment_api_key_to_environment_api_key_document,
)

from .base import BaseDynamoWrapper

if typing.TYPE_CHECKING:
    from environments.models import EnvironmentAPIKey


class DynamoEnvironmentAPIKeyWrapper(BaseDynamoWrapper):
    table_name = settings.ENVIRONMENTS_API_KEY_TABLE_NAME_DYNAMO  # type: ignore[assignment]

    def write_api_key(self, api_key: "EnvironmentAPIKey"):  # type: ignore[no-untyped-def]
        self.write_api_keys([api_key])

    def write_api_keys(self, api_keys: typing.Iterable["EnvironmentAPIKey"]):  # type: ignore[no-untyped-def]
        with self.table.batch_writer() as writer:  # type: ignore[union-attr]
            for api_key in api_keys:
                writer.put_item(
                    Item=map_environment_api_key_to_environment_api_key_document(
                        api_key
                    )
                )

    def delete_api_key(self, key: str) -> None:
        self.table.delete_item(Key={"key": key})  # type: ignore[union-attr]
