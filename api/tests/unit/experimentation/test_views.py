import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from environments.models import Environment
from experimentation.models import WarehouseConnection
from tests.types import EnableFeaturesFixture

pytestmark = pytest.mark.django_db


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


def test_post__soft_deleted_exists__resurrects_and_returns_201(
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
    assert response.json()["id"] == original_id
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


def test_post__snowflake_soft_deleted__resurrects_with_new_config(
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
            "name": "Resurrected",
            "config": {"account_identifier": "new.us-west-2"},
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] == original_id
    assert data["status"] == "created"
    assert data["name"] == "Resurrected"
    assert data["config"]["account_identifier"] == "new.us-west-2"


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
