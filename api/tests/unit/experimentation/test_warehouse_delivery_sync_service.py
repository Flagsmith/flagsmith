import json
from unittest.mock import Mock

import pytest
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture
from redis.exceptions import RedisError

from experimentation import warehouse_delivery_sync_service
from experimentation.dataclasses import WarehouseDeliveryStatus
from experimentation.warehouse_credentials import decrypt_warehouse_credentials

STATUS_KEY = "experimentation:warehouse_delivery_status"


@pytest.fixture()
def redis_client(mocker: MockerFixture, settings: SettingsWrapper) -> Mock:
    settings.INGESTION_REDIS_URL = "redis://ingestion:6379"
    client = Mock()
    mocker.patch(
        "experimentation.warehouse_delivery_sync_service.get_client",
        return_value=client,
    )
    return client


def test_publish_warehouse_connection__connection_details__writes_document_with_encrypted_credentials(
    redis_client: Mock,
) -> None:
    # Given
    config = {"host": "ch.acme-corp.example", "port": 8443, "secure": True}

    # When
    warehouse_delivery_sync_service.publish_warehouse_connection(
        "client-env-key",
        connection_id=42,
        warehouse_type="clickhouse",
        config=config,
        credentials={"password": "hunter2"},
    )

    # Then the document sits under the environment's client key, and the
    # password only ever reaches Redis as the ciphertext the database holds
    redis_client.set.assert_called_once()
    redis_key, raw = redis_client.set.call_args.args
    assert redis_key == "experimentation:environment_warehouses:client-env-key"
    assert "hunter2" not in raw
    document = json.loads(raw)
    assert document["connection_id"] == 42
    assert document["warehouse_type"] == "clickhouse"
    assert document["config"] == config
    assert decrypt_warehouse_credentials(document["credentials"]) == {
        "password": "hunter2"
    }


def test_publish_warehouse_connection__no_credentials__writes_null(
    redis_client: Mock,
) -> None:
    # Given a warehouse type the API stores no credentials for

    # When
    warehouse_delivery_sync_service.publish_warehouse_connection(
        "client-env-key",
        connection_id=42,
        warehouse_type="snowflake",
        config={"account_identifier": "acme"},
        credentials=None,
    )

    # Then
    _, raw = redis_client.set.call_args.args
    assert json.loads(raw)["credentials"] is None


def test_remove_warehouse_connection__connection_ids__deletes_document_and_outcomes(
    redis_client: Mock,
) -> None:
    # Given

    # When
    warehouse_delivery_sync_service.remove_warehouse_connection(
        "client-env-key", connection_ids=[42, 43]
    )

    # Then the delivery service stops finding the environment, and any failure
    # it recorded for these connections can no longer be shown
    redis_client.delete.assert_called_once_with(
        "experimentation:environment_warehouses:client-env-key",
    )
    redis_client.hdel.assert_called_once_with(STATUS_KEY, "42", "43")


def test_remove_warehouse_connection__no_connection_ids__deletes_document_only(
    redis_client: Mock,
) -> None:
    # Given an environment that never had a connection to forget outcomes for

    # When
    warehouse_delivery_sync_service.remove_warehouse_connection(
        "client-env-key", connection_ids=[]
    )

    # Then
    redis_client.delete.assert_called_once()
    redis_client.hdel.assert_not_called()


def test_get_warehouse_delivery_statuses__outcomes_in_hash__returned_by_connection(
    redis_client: Mock,
) -> None:
    # Given outcomes for two of three connections, as Redis hands them back
    redis_client.hmget.return_value = [
        b'{"status": "errored", "detail": "Authentication failed.", "at": 1758000000.0}',
        None,
        b'{"status": "connected", "detail": null, "at": 1758000001.0}',
    ]

    # When
    statuses = warehouse_delivery_sync_service.get_warehouse_delivery_statuses(
        [42, 43, 7]
    )

    # Then one round trip fetches them all, and the connection with no
    # outcome is simply absent
    redis_client.hmget.assert_called_once_with(STATUS_KEY, ["42", "43", "7"])
    assert statuses == {
        42: WarehouseDeliveryStatus(
            connection_id=42, status="errored", detail="Authentication failed."
        ),
        7: WarehouseDeliveryStatus(connection_id=7, status="connected", detail=None),
    }


def test_get_warehouse_delivery_statuses__unreadable_outcome__skipped_and_logged(
    redis_client: Mock,
    log: StructuredLogCapture,
) -> None:
    # Given one value that is not JSON next to a good one
    redis_client.hmget.return_value = [b"not json", b'{"status": "connected"}']

    # When
    statuses = warehouse_delivery_sync_service.get_warehouse_delivery_statuses([42, 7])

    # Then the good one still gets through
    assert list(statuses) == [7]
    assert log.has("delivery_status.unreadable", level="warning", connection__id=42)


def test_get_warehouse_delivery_statuses__redis_unavailable__returns_nothing_and_logs(
    redis_client: Mock,
    log: StructuredLogCapture,
) -> None:
    # Given the ingestion Redis does not answer
    redis_client.hmget.side_effect = RedisError("timeout")

    # When
    statuses = warehouse_delivery_sync_service.get_warehouse_delivery_statuses([42])

    # Then the caller falls back to the stored status rather than failing
    assert statuses == {}
    assert log.has("delivery_status.unavailable", level="warning")


def test_get_warehouse_delivery_statuses__redis_not_configured__returns_nothing(
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given a self-hosted installation with no ingestion Redis
    settings.INGESTION_REDIS_URL = ""
    get_client = mocker.patch(
        "experimentation.warehouse_delivery_sync_service.get_client"
    )

    # When
    statuses = warehouse_delivery_sync_service.get_warehouse_delivery_statuses([42])

    # Then Redis is not even contacted
    assert statuses == {}
    get_client.assert_not_called()


def test_get_warehouse_delivery_statuses__no_connections__returns_nothing(
    redis_client: Mock,
) -> None:
    # Given / When
    statuses = warehouse_delivery_sync_service.get_warehouse_delivery_statuses([])

    # Then
    assert statuses == {}
    redis_client.hmget.assert_not_called()
