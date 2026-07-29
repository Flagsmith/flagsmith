import gzip
from collections.abc import Iterator
from typing import Any

import boto3
import pytest
from clickhouse_connect.driver.exceptions import DatabaseError, OperationalError
from moto import mock_s3  # type: ignore[import-untyped]
from pytest_mock import MockerFixture
from urllib3 import PoolManager

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
    # Given an events bucket with no objects

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
            pool_mgr=mocker.ANY,
        )
        # Redirects must not be followed: the internal-address guard only
        # validates the host being dialled.
        pool_manager = get_client.call_args.kwargs["pool_mgr"]
        assert isinstance(
            pool_manager,
            warehouse_delivery_service._NoRedirectPoolManager,
        )
        get_client.return_value.close.assert_not_called()

    get_client.return_value.close.assert_called_once_with()


def test_delivery_client__body_raises__still_closes_client(
    clickhouse_connection: WarehouseConnection,
    mocker: MockerFixture,
) -> None:
    # Given
    get_client = mocker.patch(
        "experimentation.warehouse_delivery_service.clickhouse_connect.get_client",
    )

    # When a delivery inside the block fails
    with pytest.raises(RuntimeError, match="boom"):
        with warehouse_delivery_service.delivery_client(clickhouse_connection):
            raise RuntimeError("boom")

    # Then the pooled HTTP connection is still released
    get_client.return_value.close.assert_called_once_with()


def test_deliver_object__valid_object__streams_body_and_returns_written_rows(
    events_bucket: Any,
    mocker: MockerFixture,
) -> None:
    # Given
    events_bucket.put_object(Bucket=BUCKET_NAME, Key=_event_key("13"), Body=OBJECT_BODY)
    client = mocker.MagicMock()
    streamed_bodies: list[bytes] = []

    def raw_insert(*args: Any, **kwargs: Any) -> Any:
        streamed_bodies.append(kwargs["insert_block"].read())
        return mocker.Mock(written_rows=203)

    client.raw_insert.side_effect = raw_insert

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
    )
    # The body reaches ClickHouse as the exact bytes stored in S3, and is
    # closed once delivered
    assert streamed_bodies == [OBJECT_BODY]
    with pytest.raises(ValueError, match="closed file"):
        client.raw_insert.call_args.kwargs["insert_block"].read()


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


@pytest.mark.parametrize(
    "error, expected_detail",
    [
        pytest.param(
            warehouse_delivery_service.DeliveryConfigError(
                "Stored connection details are incomplete."
            ),
            "Stored connection details are incomplete.",
            id="config-error",
        ),
        pytest.param(
            OperationalError("HTTPSConnectionPool: Max retries exceeded"),
            "Could not connect to the host.",
            id="unreachable",
        ),
        pytest.param(
            DatabaseError("Code: 516. DB::Exception: nope", code=516),
            "Authentication failed.",
            id="bad-auth",
        ),
        pytest.param(
            DatabaseError("Code: 60. DB::Exception: no table", code=60),
            "Table `events` does not exist.",
            id="missing-table",
        ),
        pytest.param(
            DatabaseError("Code: 241. DB::Exception: memory limit", code=241),
            "The ClickHouse server rejected the request.",
            id="other-server-error",
        ),
        pytest.param(
            ConnectionResetError("connection reset by peer"),
            "Delivery failed.",
            id="unexpected-error",
        ),
    ],
)
def test_describe_delivery_error__known_failures__returns_user_facing_detail(
    error: Exception,
    expected_detail: str,
) -> None:
    # Given a parametrised delivery failure

    # When
    detail = warehouse_delivery_service.describe_delivery_error(error)

    # Then
    assert detail == expected_detail


def test_no_redirect_pool_manager__urlopen__refuses_to_follow_redirects(
    mocker: MockerFixture,
) -> None:
    # Given a manager asked to follow redirects, as clickhouse-connect's own
    # request path does
    urlopen = mocker.patch.object(PoolManager, "urlopen")
    manager = warehouse_delivery_service._NoRedirectPoolManager()

    # When
    manager.urlopen("POST", "https://ch.acme-corp.example/", redirect=True)

    # Then the redirect is refused: a permitted host must not be able to bounce
    # the request, and its event payload, to an unchecked address
    assert urlopen.call_args.kwargs["redirect"] is False
