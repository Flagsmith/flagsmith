import json

from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from experimentation import warehouse_delivery_sync_service
from experimentation.dataclasses import WarehouseDeliveryStatus
from experimentation.warehouse_credentials import decrypt_warehouse_credentials


def test_publish_warehouse_connection__connection_details__writes_document_with_encrypted_credentials(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.warehouse_delivery_sync_service.get_client",
        return_value=mock_client,
    )
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


def test_publish_warehouse_connection__no_credentials__writes_null(
    mocker: MockerFixture,
) -> None:
    # Given a warehouse type the API stores no credentials for
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.warehouse_delivery_sync_service.get_client",
        return_value=mock_client,
    )

    # When
    warehouse_delivery_sync_service.publish_warehouse_connection(
        "client-env-key",
        connection_id=42,
        warehouse_type="snowflake",
        config={"account_identifier": "acme"},
        credentials=None,
    )

    # Then
    _, raw = mock_client.set.call_args.args
    assert json.loads(raw)["credentials"] is None


def test_remove_warehouse_connection__client_key__deletes_from_redis(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.Mock()
    mocker.patch(
        "experimentation.warehouse_delivery_sync_service.get_client",
        return_value=mock_client,
    )

    # When
    warehouse_delivery_sync_service.remove_warehouse_connection("client-env-key")

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
        "experimentation.warehouse_delivery_sync_service.get_client",
        return_value=mock_client,
    )

    # When
    statuses = warehouse_delivery_sync_service.pop_warehouse_delivery_statuses()

    # Then both are returned, and the hash was read and deleted by one script
    # so nothing written in between is lost
    assert statuses == [
        WarehouseDeliveryStatus(
            connection_id=42, status="errored", detail="Authentication failed."
        ),
        WarehouseDeliveryStatus(connection_id=7, status="connected", detail=None),
    ]
    mock_client.eval.assert_called_once_with(
        warehouse_delivery_sync_service._POP_HASH_SCRIPT,
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
        "experimentation.warehouse_delivery_sync_service.get_client",
        return_value=mock_client,
    )

    # When / Then
    assert warehouse_delivery_sync_service.pop_warehouse_delivery_statuses() == []


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
        "experimentation.warehouse_delivery_sync_service.get_client",
        return_value=mock_client,
    )

    # When
    statuses = warehouse_delivery_sync_service.pop_warehouse_delivery_statuses()

    # Then the good entry still gets through
    assert statuses == [
        WarehouseDeliveryStatus(connection_id=7, status="connected", detail=None)
    ]
    assert log.has("delivery_status.unreadable", level="warning", field="not-an-id")
    assert log.has("delivery_status.unreadable", level="warning", field="42")
