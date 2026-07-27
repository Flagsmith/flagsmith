import gzip
from collections.abc import Iterator
from typing import Any

import boto3
import pytest
from clickhouse_connect.driver.exceptions import DatabaseError
from moto import mock_s3  # type: ignore[import-untyped]
from pytest_mock import MockerFixture

from experimentation import warehouse_delivery_service
from experimentation.models import WarehouseConnection

BUCKET_NAME = "flagsmith-events-lake-org-42-123456789012-eu-west-2-an"
ENVIRONMENT_KEY = "delivery_env_key"
OBJECT_BODY = gzip.compress(
    b'{"environment_key":"delivery_env_key","event":"$flag_exposure",'
    b'"timestamp":1753000000000}\n'
)


def _event_key(hour: str, environment_key: str = ENVIRONMENT_KEY) -> str:
    return (
        f"events/env_key={environment_key}/year=2026/month=07/day=27/"
        f"hour={hour}/object.gz"
    )


@pytest.fixture()
def aws_backends(aws_credentials: None) -> Iterator[None]:
    warehouse_delivery_service._get_s3_client.cache_clear()
    with mock_s3():
        yield
    warehouse_delivery_service._get_s3_client.cache_clear()


@pytest.fixture()
def events_bucket(aws_backends: None) -> Any:
    s3 = boto3.client("s3", region_name="eu-west-2")
    s3.create_bucket(
        Bucket=BUCKET_NAME,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )
    return s3


def test_list_pending_objects__objects_across_hours__returns_chronological_and_scoped(
    events_bucket: Any,
) -> None:
    # Given objects for two hours, put out of order, plus another
    # environment's object in the same bucket
    events_bucket.put_object(Bucket=BUCKET_NAME, Key=_event_key("14"), Body=OBJECT_BODY)
    events_bucket.put_object(Bucket=BUCKET_NAME, Key=_event_key("13"), Body=OBJECT_BODY)
    events_bucket.put_object(
        Bucket=BUCKET_NAME,
        Key=_event_key("13", environment_key="other_env_key"),
        Body=OBJECT_BODY,
    )

    # When
    pending = warehouse_delivery_service.list_pending_objects(
        BUCKET_NAME,
        environment_key=ENVIRONMENT_KEY,
    )

    # Then
    assert pending == [_event_key("13"), _event_key("14")]


def test_list_pending_objects__no_objects__returns_empty(
    events_bucket: Any,
) -> None:
    # When
    pending = warehouse_delivery_service.list_pending_objects(
        BUCKET_NAME,
        environment_key=ENVIRONMENT_KEY,
    )

    # Then
    assert pending == []


def test_move_object__to_archive__moves_and_preserves_partition_path(
    events_bucket: Any,
) -> None:
    # Given
    events_bucket.put_object(Bucket=BUCKET_NAME, Key=_event_key("13"), Body=OBJECT_BODY)

    # When
    destination_key = warehouse_delivery_service.move_object(
        BUCKET_NAME,
        _event_key("13"),
        to_prefix=warehouse_delivery_service.ARCHIVE_PREFIX,
    )

    # Then
    assert destination_key == (
        f"archive/env_key={ENVIRONMENT_KEY}/year=2026/month=07/day=27/hour=13/object.gz"
    )
    archived = events_bucket.get_object(Bucket=BUCKET_NAME, Key=destination_key)
    assert archived["Body"].read() == OBJECT_BODY
    assert (
        warehouse_delivery_service.list_pending_objects(
            BUCKET_NAME,
            environment_key=ENVIRONMENT_KEY,
        )
        == []
    )


def test_delivery_client__incomplete_config__raises_config_error(
    clickhouse_connection: WarehouseConnection,
) -> None:
    # Given
    clickhouse_connection.credentials = None

    # When / Then
    with pytest.raises(
        warehouse_delivery_service.DeliveryConfigError,
        match="incomplete",
    ):
        with warehouse_delivery_service.delivery_client(clickhouse_connection):
            pass  # pragma: no cover


def test_delivery_client__internal_host__raises_config_error(
    clickhouse_connection: WarehouseConnection,
) -> None:
    # Given
    clickhouse_connection.config["host"] = "10.13.37.1"  # type: ignore[index]

    # When / Then
    with pytest.raises(
        warehouse_delivery_service.DeliveryConfigError,
        match="internal or private",
    ):
        with warehouse_delivery_service.delivery_client(clickhouse_connection):
            pass  # pragma: no cover


def test_delivery_client__unmappable_port__raises_config_error(
    clickhouse_connection: WarehouseConnection,
) -> None:
    # Given
    clickhouse_connection.config["port"] = 1234  # type: ignore[index]

    # When / Then
    with pytest.raises(
        warehouse_delivery_service.DeliveryConfigError,
        match="No HTTP port is known for ClickHouse port 1234",
    ):
        with warehouse_delivery_service.delivery_client(clickhouse_connection):
            pass  # pragma: no cover


def test_delivery_client__valid_config__yields_http_client_and_closes(
    clickhouse_connection: WarehouseConnection,
    mocker: MockerFixture,
) -> None:
    # Given
    get_client = mocker.patch(
        "experimentation.warehouse_delivery_service.clickhouse_connect.get_client",
    )

    # When
    with warehouse_delivery_service.delivery_client(clickhouse_connection) as client:
        # Then the native port is mapped to its HTTP counterpart
        assert client is get_client.return_value
        get_client.assert_called_once_with(
            host="ch.acme-corp.example",
            port=8443,
            username="acme_svc",
            password="hunter2",
            database="acme_dwh",
            secure=True,
            connect_timeout=10,
            send_receive_timeout=300,
        )
        get_client.return_value.close.assert_not_called()

    get_client.return_value.close.assert_called_once_with()


def test_deliver_object__valid_object__streams_body_and_returns_written_rows(
    events_bucket: Any,
    mocker: MockerFixture,
) -> None:
    # Given
    events_bucket.put_object(Bucket=BUCKET_NAME, Key=_event_key("13"), Body=OBJECT_BODY)
    client = mocker.MagicMock()
    client.raw_insert.return_value.written_rows = 203

    # When
    written_rows = warehouse_delivery_service.deliver_object(
        client,
        BUCKET_NAME,
        _event_key("13"),
    )

    # Then
    assert written_rows == 203
    client.raw_insert.assert_called_once_with(
        "events",
        insert_block=mocker.ANY,
        fmt="JSONEachRow",
        compression="gzip",
        settings={"insert_deduplication_token": _event_key("13")},
    )
    # The body reaches ClickHouse as the exact bytes stored in S3
    insert_block = client.raw_insert.call_args.kwargs["insert_block"]
    assert insert_block.read() == OBJECT_BODY


def test_deliver_object__object_level_error__raises_object_rejected(
    events_bucket: Any,
    mocker: MockerFixture,
) -> None:
    # Given a warehouse that rejects the object's contents (469 =
    # VIOLATED_CONSTRAINT)
    events_bucket.put_object(Bucket=BUCKET_NAME, Key=_event_key("13"), Body=OBJECT_BODY)
    client = mocker.MagicMock()
    client.raw_insert.side_effect = DatabaseError(
        "Constraint `event_not_empty` violated",
        code=469,
    )

    # When / Then
    with pytest.raises(warehouse_delivery_service.ObjectRejectedError):
        warehouse_delivery_service.deliver_object(
            client,
            BUCKET_NAME,
            _event_key("13"),
        )


def test_deliver_object__connection_level_error__reraises(
    events_bucket: Any,
    mocker: MockerFixture,
) -> None:
    # Given a warehouse failure unrelated to the object's contents (516 =
    # AUTHENTICATION_FAILED)
    events_bucket.put_object(Bucket=BUCKET_NAME, Key=_event_key("13"), Body=OBJECT_BODY)
    client = mocker.MagicMock()
    client.raw_insert.side_effect = DatabaseError(
        "Authentication failed",
        code=516,
    )

    # When / Then
    with pytest.raises(DatabaseError):
        warehouse_delivery_service.deliver_object(
            client,
            BUCKET_NAME,
            _event_key("13"),
        )
