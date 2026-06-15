import pytest
from django.urls import reverse
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from environments.models import Environment
from experimentation import services
from experimentation.dataclasses import WarehouseEventStats
from experimentation.models import (
    WarehouseConnection,
    WarehouseConnectionStatus,
    WarehouseType,
)
from tests.types import EnableFeaturesFixture

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def mock_clickhouse_stats(
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> object:
    """Default every view test to a configured, empty warehouse. Tests that need
    events re-patch experimentation.services.get_warehouse_event_stats; tests for the
    unconfigured/erroring paths override the setting / raise."""
    settings.EXPERIMENTATION_CLICKHOUSE_URL = "clickhouse://localhost:9000/test"
    services._get_clickhouse_client.cache_clear()
    mock_client = mocker.Mock()
    mock_client.execute.return_value = [(0, 0)]
    return mocker.patch(
        "experimentation.services._get_clickhouse_client",
        return_value=mock_client,
    )


def test_post__valid_data__returns_201_and_creates_connection(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection_url: str,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")

    # When
    response = admin_client.post(
        warehouse_connection_url,
        data={"warehouse_type": "flagsmith"},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["warehouse_type"] == "flagsmith"
    assert response.json()["status"] == "created"
    assert response.json()["name"] == f"Flagsmith Warehouse - {environment.name}"
    assert response.json()["config"] is None
    assert "id" in response.json()
    assert "created_at" in response.json()
    assert WarehouseConnection.objects.filter(environment=environment).count() == 1


def test_post__already_exists__returns_409(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection: WarehouseConnection,
    warehouse_connection_url: str,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")

    # When
    response = admin_client.post(
        warehouse_connection_url,
        data={"warehouse_type": "flagsmith"},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_409_CONFLICT
    assert (
        response.json()["detail"]
        == "This environment already has an active warehouse connection."
    )


def test_post__different_type_already_exists__returns_409(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection: WarehouseConnection,
    warehouse_connection_url: str,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")

    # When
    response = admin_client.post(
        warehouse_connection_url,
        data={
            "warehouse_type": "snowflake",
            "name": "My Snowflake",
            "config": {"account_identifier": "xy12345.us-east-1"},
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_409_CONFLICT
    assert (
        response.json()["detail"]
        == "This environment already has an active warehouse connection."
    )


def test_post__soft_deleted_exists__creates_new_record_and_returns_201(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection: WarehouseConnection,
    warehouse_connection_url: str,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    original_id = warehouse_connection.id
    warehouse_connection.delete()

    # When
    response = admin_client.post(
        warehouse_connection_url,
        data={"warehouse_type": "flagsmith"},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["id"] != original_id
    assert response.json()["status"] == "created"


def test_post__non_admin__returns_403(
    staff_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    url = reverse(
        "api-v1:environments:experimentation:warehouse-connections-list",
        args=[environment.api_key],
    )

    # When
    response = staff_client.post(
        url,
        data={"warehouse_type": "flagsmith"},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_post__valid_data__creates_audit_log(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection_url: str,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")

    # When
    admin_client.post(
        warehouse_connection_url,
        data={"warehouse_type": "flagsmith"},
        format="json",
    )

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.WAREHOUSE_CONNECTION.name,
        ).count()
        == 1
    )
    audit_log = AuditLog.objects.get(
        related_object_type=RelatedObjectType.WAREHOUSE_CONNECTION.name,
    )
    assert "created" in audit_log.log
    assert environment.name in audit_log.log


def test_get__exists__returns_200_with_list(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection: WarehouseConnection,
    warehouse_connection_url: str,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")

    # When
    response = admin_client.get(warehouse_connection_url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["warehouse_type"] == "flagsmith"
    assert data[0]["status"] == "created"
    assert data[0]["name"] == f"Flagsmith Warehouse - {environment.name}"
    assert data[0]["id"] == warehouse_connection.id
    assert "created_at" in data[0]


def test_get__not_exists__returns_200_with_empty_list(
    admin_client: APIClient,
    enable_features: EnableFeaturesFixture,
    warehouse_connection_url: str,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")

    # When
    response = admin_client.get(warehouse_connection_url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_delete__exists__returns_204(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection: WarehouseConnection,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    url = reverse(
        "api-v1:environments:experimentation:warehouse-connections-detail",
        args=[environment.api_key, warehouse_connection.id],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert WarehouseConnection.objects.filter(environment=environment).count() == 0
    deleted = WarehouseConnection.objects.all_with_deleted().get(
        pk=warehouse_connection.pk,
    )
    assert deleted.deleted_at is not None


def test_delete__not_exists__returns_404(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    url = reverse(
        "api-v1:environments:experimentation:warehouse-connections-detail",
        args=[environment.api_key, 999999],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete__exists__creates_audit_log(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection: WarehouseConnection,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    url = reverse(
        "api-v1:environments:experimentation:warehouse-connections-detail",
        args=[environment.api_key, warehouse_connection.id],
    )

    # When
    admin_client.delete(url)

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.WAREHOUSE_CONNECTION.name,
        ).count()
        == 1
    )
    audit_log = AuditLog.objects.get(
        related_object_type=RelatedObjectType.WAREHOUSE_CONNECTION.name,
    )
    assert "deleted" in audit_log.log
    assert environment.name in audit_log.log


def test_get_detail__exists__returns_200(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection: WarehouseConnection,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    url = reverse(
        "api-v1:environments:experimentation:warehouse-connections-detail",
        args=[environment.api_key, warehouse_connection.id],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == warehouse_connection.id
    assert data["warehouse_type"] == "flagsmith"
    assert data["status"] == "created"
    assert data["name"] == f"Flagsmith Warehouse - {environment.name}"
    assert "created_at" in data


def test_get_detail__not_exists__returns_404(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    url = reverse(
        "api-v1:environments:experimentation:warehouse-connections-detail",
        args=[environment.api_key, 999999],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_post__snowflake_valid_config__returns_201(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection_url: str,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    config = {
        "account_identifier": "xy12345.us-east-1",
        "warehouse": "MY_WH",
        "database": "MY_DB",
        "schema": "MY_SCHEMA",
        "role": "MY_ROLE",
        "user": "MY_USER",
    }

    # When
    response = admin_client.post(
        warehouse_connection_url,
        data={
            "warehouse_type": "snowflake",
            "name": "My Snowflake",
            "config": config,
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["warehouse_type"] == "snowflake"
    assert data["status"] == "created"
    assert data["name"] == "My Snowflake"
    assert data["config"] == config


def test_post__snowflake_minimal_config__applies_defaults(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection_url: str,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")

    # When
    response = admin_client.post(
        warehouse_connection_url,
        data={
            "warehouse_type": "snowflake",
            "name": "Minimal Snowflake",
            "config": {"account_identifier": "xy12345.us-east-1"},
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["config"]["account_identifier"] == "xy12345.us-east-1"
    assert data["config"]["warehouse"] == "COMPUTE_WH"
    assert data["config"]["database"] == "FLAGSMITH"
    assert data["config"]["schema"] == "ANALYTICS"
    assert data["config"]["role"] == "FLAGSMITH_LOADER"
    assert data["config"]["user"] == "FLAGSMITH_SERVICE"


def test_post__snowflake_missing_account_identifier__returns_400(
    admin_client: APIClient,
    enable_features: EnableFeaturesFixture,
    warehouse_connection_url: str,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")

    # When
    response = admin_client.post(
        warehouse_connection_url,
        data={
            "warehouse_type": "snowflake",
            "name": "Bad Snowflake",
            "config": {"warehouse": "MY_WH"},
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_post__flagsmith_with_config__returns_400(
    admin_client: APIClient,
    enable_features: EnableFeaturesFixture,
    warehouse_connection_url: str,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")

    # When
    response = admin_client.post(
        warehouse_connection_url,
        data={
            "warehouse_type": "flagsmith",
            "config": {"account_identifier": "should-not-be-here"},
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_post__custom_name__uses_provided_name(
    admin_client: APIClient,
    enable_features: EnableFeaturesFixture,
    warehouse_connection_url: str,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")

    # When
    response = admin_client.post(
        warehouse_connection_url,
        data={"warehouse_type": "flagsmith", "name": "My Custom Name"},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "My Custom Name"


def test_post__snowflake_no_name__auto_generates_name(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection_url: str,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")

    # When
    response = admin_client.post(
        warehouse_connection_url,
        data={
            "warehouse_type": "snowflake",
            "config": {"account_identifier": "xy12345.us-east-1"},
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == f"Snowflake Warehouse - {environment.name}"


def test_post__snowflake_soft_deleted__creates_new_record_with_new_config(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection_url: str,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    create_response = admin_client.post(
        warehouse_connection_url,
        data={
            "warehouse_type": "snowflake",
            "name": "Original",
            "config": {"account_identifier": "old.us-east-1"},
        },
        format="json",
    )
    original_id = create_response.json()["id"]
    url = reverse(
        "api-v1:environments:experimentation:warehouse-connections-detail",
        args=[environment.api_key, original_id],
    )
    admin_client.delete(url)

    # When
    response = admin_client.post(
        warehouse_connection_url,
        data={
            "warehouse_type": "snowflake",
            "name": "Replacement",
            "config": {"account_identifier": "new.us-west-2"},
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] != original_id
    assert data["status"] == "created"
    assert data["name"] == "Replacement"
    assert data["config"]["account_identifier"] == "new.us-west-2"


def test_post__different_type_soft_deleted__creates_new_record(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection_url: str,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    create_response = admin_client.post(
        warehouse_connection_url,
        data={
            "warehouse_type": "snowflake",
            "name": "Old Snowflake",
            "config": {"account_identifier": "xy12345.us-east-1"},
        },
        format="json",
    )
    original_id = create_response.json()["id"]
    url = reverse(
        "api-v1:environments:experimentation:warehouse-connections-detail",
        args=[environment.api_key, original_id],
    )
    admin_client.delete(url)

    # When
    response = admin_client.post(
        warehouse_connection_url,
        data={"warehouse_type": "flagsmith"},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] != original_id
    assert data["warehouse_type"] == "flagsmith"


def test_patch__snowflake_update_config__returns_200(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection_url: str,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    create_response = admin_client.post(
        warehouse_connection_url,
        data={
            "warehouse_type": "snowflake",
            "name": "My Snowflake",
            "config": {"account_identifier": "xy12345.us-east-1"},
        },
        format="json",
    )
    connection_id = create_response.json()["id"]
    url = reverse(
        "api-v1:environments:experimentation:warehouse-connections-detail",
        args=[environment.api_key, connection_id],
    )

    # When
    response = admin_client.patch(
        url,
        data={"config": {"account_identifier": "new.us-west-2", "warehouse": "BIG_WH"}},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["config"]["account_identifier"] == "new.us-west-2"
    assert data["config"]["warehouse"] == "BIG_WH"


def test_patch__snowflake_update_name__returns_200(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection_url: str,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    create_response = admin_client.post(
        warehouse_connection_url,
        data={
            "warehouse_type": "snowflake",
            "name": "Original Name",
            "config": {"account_identifier": "xy12345.us-east-1"},
        },
        format="json",
    )
    connection_id = create_response.json()["id"]
    url = reverse(
        "api-v1:environments:experimentation:warehouse-connections-detail",
        args=[environment.api_key, connection_id],
    )

    # When
    response = admin_client.patch(
        url,
        data={"name": "Updated Name"},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Updated Name"


def test_patch__flagsmith_update_name__returns_200(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection: WarehouseConnection,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    url = reverse(
        "api-v1:environments:experimentation:warehouse-connections-detail",
        args=[environment.api_key, warehouse_connection.id],
    )

    # When
    response = admin_client.patch(
        url,
        data={"name": "New Flagsmith Name"},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "New Flagsmith Name"


def test_patch__flagsmith_add_config__returns_400(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection: WarehouseConnection,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    url = reverse(
        "api-v1:environments:experimentation:warehouse-connections-detail",
        args=[environment.api_key, warehouse_connection.id],
    )

    # When
    response = admin_client.patch(
        url,
        data={"config": {"account_identifier": "nope"}},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_patch__non_admin__returns_403(
    staff_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection: WarehouseConnection,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    url = reverse(
        "api-v1:environments:experimentation:warehouse-connections-detail",
        args=[environment.api_key, warehouse_connection.id],
    )

    # When
    response = staff_client.patch(
        url,
        data={"name": "Hacked"},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_patch__exists__creates_audit_log(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection: WarehouseConnection,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    url = reverse(
        "api-v1:environments:experimentation:warehouse-connections-detail",
        args=[environment.api_key, warehouse_connection.id],
    )

    # When
    admin_client.patch(
        url,
        data={"name": "Renamed"},
        format="json",
    )

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.WAREHOUSE_CONNECTION.name,
        ).count()
        == 1
    )
    audit_log = AuditLog.objects.get(
        related_object_type=RelatedObjectType.WAREHOUSE_CONNECTION.name,
    )
    assert "updated" in audit_log.log


@pytest.mark.parametrize(
    "warehouse_type, config, expected_total, expected_unique",
    [
        (WarehouseType.FLAGSMITH, None, 12, 3),
        (
            WarehouseType.SNOWFLAKE,
            {"account_identifier": "xy12345.us-east-1"},
            None,
            None,
        ),
    ],
    ids=["flagsmith", "snowflake"],
)
def test_get__warehouse_type__returns_expected_event_stats(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection_url: str,
    mocker: MockerFixture,
    warehouse_type: str,
    config: dict[str, str] | None,
    expected_total: int | None,
    expected_unique: int | None,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=warehouse_type,
        name="Warehouse",
        config=config,
    )
    mocker.patch(
        "experimentation.services.get_warehouse_event_stats",
        return_value=WarehouseEventStats(
            total_events_received=12,
            unique_events_count=3,
        ),
    )

    # When
    response = admin_client.get(warehouse_connection_url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()[0]
    assert data["total_events_received"] == expected_total
    assert data["unique_events_count"] == expected_unique


def test_get__pending_connection_with_events__shows_stats_but_does_not_flip(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection_url: str,
    mocker: MockerFixture,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    connection = WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.FLAGSMITH,
        name="Flagsmith Warehouse",
        status=WarehouseConnectionStatus.PENDING_CONNECTION,
    )
    mocker.patch(
        "experimentation.services.get_warehouse_event_stats",
        return_value=WarehouseEventStats(
            total_events_received=1,
            unique_events_count=1,
        ),
    )

    # When
    response = admin_client.get(warehouse_connection_url)

    # Then
    data = response.json()[0]
    assert data["total_events_received"] == 1
    assert data["unique_events_count"] == 1
    # GET is read-only: the flip happens on the POST endpoint, not here.
    assert data["status"] == "pending_connection"
    connection.refresh_from_db()
    assert connection.status == WarehouseConnectionStatus.PENDING_CONNECTION


@pytest.mark.parametrize(
    "warehouse_type, config, expected_status",
    [
        (WarehouseType.FLAGSMITH, None, status.HTTP_200_OK),
        (
            WarehouseType.SNOWFLAKE,
            {"account_identifier": "xy12345.us-east-1"},
            status.HTTP_400_BAD_REQUEST,
        ),
    ],
    ids=["flagsmith", "snowflake"],
)
def test_test_warehouse_connection__warehouse_type__expected_status(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_type: str,
    config: dict[str, str] | None,
    expected_status: int,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    connection = WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=warehouse_type,
        name="Warehouse",
        config=config,
    )
    url = reverse(
        "api-v1:environments:experimentation:warehouse-connections-test-warehouse-connection",
        args=[environment.api_key, connection.id],
    )

    # When
    response = admin_client.post(url, format="json")

    # Then
    assert response.status_code == expected_status
    if expected_status == status.HTTP_200_OK:
        assert response.json()["status"] == "pending_connection"
        connection.refresh_from_db()
        assert connection.status == WarehouseConnectionStatus.PENDING_CONNECTION


def test_test_warehouse_connection__pending_with_events__flips_to_connected(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    mocker: MockerFixture,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    connection = WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.FLAGSMITH,
        name="Flagsmith Warehouse",
        status=WarehouseConnectionStatus.PENDING_CONNECTION,
    )
    mocker.patch(
        "experimentation.services.get_warehouse_event_stats",
        return_value=WarehouseEventStats(
            total_events_received=1,
            unique_events_count=1,
        ),
    )
    url = reverse(
        "api-v1:environments:experimentation:warehouse-connections-test-warehouse-connection",
        args=[environment.api_key, connection.id],
    )

    # When
    response = admin_client.post(url, format="json")

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "connected"
    connection.refresh_from_db()
    assert connection.status == WarehouseConnectionStatus.CONNECTED


def test_test_warehouse_connection__pending_no_events__stays_pending(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given (autouse mock returns 0 events)
    enable_features("experimentation_warehouse_connection")
    connection = WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.FLAGSMITH,
        name="Flagsmith Warehouse",
        status=WarehouseConnectionStatus.PENDING_CONNECTION,
    )
    url = reverse(
        "api-v1:environments:experimentation:warehouse-connections-test-warehouse-connection",
        args=[environment.api_key, connection.id],
    )

    # When
    response = admin_client.post(url, format="json")

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "pending_connection"
    connection.refresh_from_db()
    assert connection.status == WarehouseConnectionStatus.PENDING_CONNECTION


def test_test_warehouse_connection__clickhouse_unreachable__stays_pending(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    mocker: MockerFixture,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    connection = WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.FLAGSMITH,
        name="Flagsmith Warehouse",
        status=WarehouseConnectionStatus.PENDING_CONNECTION,
    )
    mocker.patch(
        "experimentation.services.get_warehouse_event_stats",
        side_effect=OSError("clickhouse unreachable"),
    )
    url = reverse(
        "api-v1:environments:experimentation:warehouse-connections-test-warehouse-connection",
        args=[environment.api_key, connection.id],
    )

    # When
    response = admin_client.post(url, format="json")

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "pending_connection"
    assert data["total_events_received"] is None
    assert data["unique_events_count"] is None


def test_test_warehouse_connection__already_connected__is_noop(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    connection = WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.FLAGSMITH,
        name="Flagsmith Warehouse",
        status=WarehouseConnectionStatus.CONNECTED,
    )
    url = reverse(
        "api-v1:environments:experimentation:warehouse-connections-test-warehouse-connection",
        args=[environment.api_key, connection.id],
    )

    # When
    response = admin_client.post(url, format="json")

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "connected"


def test_test_warehouse_connection__non_admin__returns_403(
    staff_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection: WarehouseConnection,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    url = reverse(
        "api-v1:environments:experimentation:warehouse-connections-test-warehouse-connection",
        args=[environment.api_key, warehouse_connection.id],
    )

    # When
    response = staff_client.post(url, format="json")

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get__clickhouse_unconfigured__returns_200_without_stats(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection: WarehouseConnection,
    warehouse_connection_url: str,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    settings.EXPERIMENTATION_CLICKHOUSE_URL = None
    stats_spy = mocker.patch("experimentation.services.get_warehouse_event_stats")

    # When
    response = admin_client.get(warehouse_connection_url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()[0]
    assert data["total_events_received"] is None
    assert data["unique_events_count"] is None
    stats_spy.assert_not_called()


def test_get__exclude_event_stats__returns_200_without_querying_warehouse(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection: WarehouseConnection,
    warehouse_connection_url: str,
    mocker: MockerFixture,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    annotate_spy = mocker.patch("experimentation.views.annotate_warehouse_event_stats")

    # When
    response = admin_client.get(f"{warehouse_connection_url}?exclude_event_stats=true")

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()[0]
    assert data["id"] == warehouse_connection.id
    assert data["total_events_received"] is None
    assert data["unique_events_count"] is None
    annotate_spy.assert_not_called()


def test_get__clickhouse_errors__returns_200_without_stats(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    warehouse_connection_url: str,
    mocker: MockerFixture,
) -> None:
    # Given
    enable_features("experimentation_warehouse_connection")
    WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.FLAGSMITH,
        name="Flagsmith Warehouse",
        status=WarehouseConnectionStatus.PENDING_CONNECTION,
    )
    mocker.patch(
        "experimentation.services.get_warehouse_event_stats",
        side_effect=OSError("clickhouse unreachable"),
    )

    # When
    response = admin_client.get(warehouse_connection_url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()[0]
    assert data["total_events_received"] is None
    assert data["unique_events_count"] is None
    # connection stays pending (GET never writes)
    assert data["status"] == "pending_connection"
