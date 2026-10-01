import json
from unittest.mock import Mock

import pytest
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from experimentation import warehouse_delivery_sync_service
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


def test_remove_warehouse_connection__client_api_key__deletes_document(
    redis_client: Mock,
) -> None:
    # Given

    # When
    warehouse_delivery_sync_service.remove_warehouse_connection("client-env-key")

    # Then the delivery service stops finding the environment
    redis_client.delete.assert_called_once_with(
        "experimentation:environment_warehouses:client-env-key",
    )


def test_delete_warehouse_delivery_statuses__connection_ids__deletes_their_outcomes(
    redis_client: Mock,
) -> None:
    # Given

    # When
    warehouse_delivery_sync_service.delete_warehouse_delivery_statuses([42, 43])

    # Then any outcome recorded for these connections can no longer be shown
    redis_client.hdel.assert_called_once_with(STATUS_KEY, "42", "43")


def test_delete_warehouse_delivery_statuses__no_connection_ids__does_not_call_redis(
    redis_client: Mock,
) -> None:
    # Given an environment that never had a connection to forget outcomes for

    # When
    warehouse_delivery_sync_service.delete_warehouse_delivery_statuses([])

    # Then
    redis_client.hdel.assert_not_called()
