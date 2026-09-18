import json
from datetime import datetime
from datetime import timezone as dt_timezone

import pytest
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture
from redis.exceptions import RedisError

from experimentation import ingestion_sync_service
from experimentation.dataclasses import WarehouseDeliveryStatus
from experimentation.warehouse_credentials import decrypt_warehouse_credentials


def test_get_client__configured_url__builds_redis_cluster_with_socket_options(
    mocker: MockerFixture,
    settings: object,
) -> None:
    # Given
    settings.INGESTION_REDIS_URL = "redis://ingestion:6379"  # type: ignore[attr-defined]
    mock_from_url = mocker.patch(
        "experimentation.ingestion_sync_service.RedisCluster.from_url",
    )

    # When
    client = ingestion_sync_service._get_client()

    # Then
    mock_from_url.assert_called_once_with(
        "redis://ingestion:6379",
        socket_timeout=ingestion_sync_service.SOCKET_TIMEOUT,
        socket_keepalive=True,
    )
    assert client is mock_from_url.return_value


def test_set_ingestion_key__no_expiry__writes_environment_key_without_ttl(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.ingestion_sync_service._get_client",
        return_value=mock_client,
    )

    # When
    ingestion_sync_service.set_ingestion_key(
        "ser.test-key-001",
        environment_key="client-env-key",
    )

    # Then
    mock_client.set.assert_called_once_with(
        "experimentation:environment_keys:ser.test-key-001",
        "client-env-key",
        exat=None,
    )


def test_set_ingestion_key__expiry__writes_environment_key_with_ttl(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.ingestion_sync_service._get_client",
        return_value=mock_client,
    )
    expires_at = datetime(2026, 9, 1, tzinfo=dt_timezone.utc)

    # When
    ingestion_sync_service.set_ingestion_key(
        "ser.test-key-001",
        environment_key="client-env-key",
        expires_at=expires_at,
    )

    # Then
    mock_client.set.assert_called_once_with(
        "experimentation:environment_keys:ser.test-key-001",
        "client-env-key",
        exat=int(expires_at.timestamp()),
    )


def test_delete_ingestion_key__valid_key__deletes_from_redis(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.ingestion_sync_service._get_client",
        return_value=mock_client,
    )

    # When
    ingestion_sync_service.delete_ingestion_key("ser.test-key-001")

    # Then
    mock_client.delete.assert_called_once_with(
        "experimentation:environment_keys:ser.test-key-001",
    )


def test_set_ingestion_destination__valid_topic__writes_topic(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.ingestion_sync_service._get_client",
        return_value=mock_client,
    )

    # When
    ingestion_sync_service.set_ingestion_destination(
        "client-env-key",
        topic="external_warehouse_events",
    )

    # Then
    mock_client.set.assert_called_once_with(
        "experimentation:environment_destinations:client-env-key",
        "external_warehouse_events",
    )


def test_delete_ingestion_destination__valid_key__deletes_from_redis(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.ingestion_sync_service._get_client",
        return_value=mock_client,
    )

    # When
    ingestion_sync_service.delete_ingestion_destination("client-env-key")

    # Then
    mock_client.delete.assert_called_once_with(
        "experimentation:environment_destinations:client-env-key",
    )


def test_set_ingestion_key__redis_error__propagates(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mock_client.set.side_effect = RedisError("boom")
    mocker.patch(
        "experimentation.ingestion_sync_service._get_client",
        return_value=mock_client,
    )

    # When / Then
    with pytest.raises(RedisError, match="boom"):
        ingestion_sync_service.set_ingestion_key(
            "ser.test-key-001",
            environment_key="client-env-key",
        )


def test_delete_ingestion_key__redis_error__propagates(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mock_client.delete.side_effect = RedisError("boom")
    mocker.patch(
        "experimentation.ingestion_sync_service._get_client",
        return_value=mock_client,
    )

    # When / Then
    with pytest.raises(RedisError, match="boom"):
        ingestion_sync_service.delete_ingestion_key("ser.test-key-001")


def test_set_ingestion_warehouse__connection_details__writes_document_with_encrypted_credentials(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.ingestion_sync_service._get_client",
        return_value=mock_client,
    )
    config = {"host": "ch.acme-corp.example", "port": 8443, "secure": True}

    # When
    ingestion_sync_service.set_ingestion_warehouse(
        "client-env-key",
        connection_id=42,
        warehouse_type="clickhouse",
        config=config,
        credentials={"password": "hunter2"},
    )

    # Then the document sits under the environment's client key, and the
    # password only ever reaches Redis as the ciphertext the database holds
    mock_client.set.assert_called_once()
    redis_key, raw = mock_client.set.call_args.args
    assert redis_key == "experimentation:environment_warehouses:client-env-key"
    assert "hunter2" not in raw
    document = json.loads(raw)
    assert document["connection_id"] == 42
    assert document["warehouse_type"] == "clickhouse"
    assert document["config"] == config
    assert decrypt_warehouse_credentials(document["credentials"]) == {
        "password": "hunter2"
    }


def test_set_ingestion_warehouse__no_credentials__writes_null(
    mocker: MockerFixture,
) -> None:
    # Given a warehouse type the API stores no credentials for
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.ingestion_sync_service._get_client",
        return_value=mock_client,
    )

    # When
    ingestion_sync_service.set_ingestion_warehouse(
        "client-env-key",
        connection_id=42,
        warehouse_type="snowflake",
        config={"account_identifier": "acme"},
        credentials=None,
    )

    # Then
    _, raw = mock_client.set.call_args.args
    assert json.loads(raw)["credentials"] is None


def test_delete_ingestion_warehouse__client_key__deletes_from_redis(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.ingestion_sync_service._get_client",
        return_value=mock_client,
    )

    # When
    ingestion_sync_service.delete_ingestion_warehouse("client-env-key")

    # Then
    mock_client.delete.assert_called_once_with(
        "experimentation:environment_warehouses:client-env-key",
    )


def test_pop_warehouse_delivery_statuses__entries_in_hash__read_and_cleared_in_one_step(
    mocker: MockerFixture,
) -> None:
    # Given two outcomes the delivery service left, as Redis hands them back
    mock_client = mocker.Mock()
    mock_client.eval.return_value = [
        b"42",
        b'{"status": "errored", "detail": "Authentication failed.", "at": 1758000000.0}',
        b"7",
        b'{"status": "connected", "detail": null, "at": 1758000001.0}',
    ]
    mocker.patch(
        "experimentation.ingestion_sync_service._get_client",
        return_value=mock_client,
    )

    # When
    statuses = ingestion_sync_service.pop_warehouse_delivery_statuses()

    # Then both are returned, and the hash was read and deleted by one script
    # so nothing written in between is lost
    assert statuses == [
        WarehouseDeliveryStatus(
            connection_id=42, status="errored", detail="Authentication failed."
        ),
        WarehouseDeliveryStatus(connection_id=7, status="connected", detail=None),
    ]
    mock_client.eval.assert_called_once_with(
        ingestion_sync_service._POP_HASH_SCRIPT,
        1,
        "experimentation:warehouse_delivery_status",
    )


def test_pop_warehouse_delivery_statuses__empty_hash__returns_nothing(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mock_client.eval.return_value = []
    mocker.patch(
        "experimentation.ingestion_sync_service._get_client",
        return_value=mock_client,
    )

    # When / Then
    assert ingestion_sync_service.pop_warehouse_delivery_statuses() == []


def test_pop_warehouse_delivery_statuses__unreadable_entries__skipped_and_logged(
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given a field that is not a connection id, a value that is not JSON, and
    # one good entry
    mock_client = mocker.Mock()
    mock_client.eval.return_value = [
        b"not-an-id",
        b'{"status": "errored"}',
        b"42",
        b"not json",
        b"7",
        b'{"status": "connected"}',
    ]
    mocker.patch(
        "experimentation.ingestion_sync_service._get_client",
        return_value=mock_client,
    )

    # When
    statuses = ingestion_sync_service.pop_warehouse_delivery_statuses()

    # Then the good entry still gets through
    assert statuses == [
        WarehouseDeliveryStatus(connection_id=7, status="connected", detail=None)
    ]
    assert log.has("delivery_status.unreadable", level="warning", field="not-an-id")
    assert log.has("delivery_status.unreadable", level="warning", field="42")
