import pytest
from rest_framework import status
from rest_framework.test import APIClient

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from environments.models import Environment
from experimentation.models import WarehouseConnection
from tests.types import EnableFeaturesFixture
from tests.unit.experimentation.conftest import reverse_warehouse_connection_url

pytestmark = pytest.mark.django_db


class TestWarehouseConnectionViewPost:
    def test_post__valid_data__returns_201_and_creates_connection(
        self,
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
        assert response.json()["status"] == "pending_connection"
        assert response.json()["name"] == f"Flagsmith Warehouse - {environment.name}"
        assert "uuid" in response.json()
        assert "created_at" in response.json()
        assert WarehouseConnection.objects.filter(environment=environment).count() == 1

    def test_post__already_exists__returns_409(
        self,
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
        assert response.json()["detail"] == "Warehouse connection already exists."

    def test_post__soft_deleted_exists__resurrects_and_returns_201(
        self,
        admin_client: APIClient,
        environment: Environment,
        enable_features: EnableFeaturesFixture,
        warehouse_connection: WarehouseConnection,
        warehouse_connection_url: str,
    ) -> None:
        # Given
        enable_features("experimentation_warehouse_connection")
        original_uuid = str(warehouse_connection.uuid)
        warehouse_connection.delete()

        # When
        response = admin_client.post(
            warehouse_connection_url,
            data={"warehouse_type": "flagsmith"},
            format="json",
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["uuid"] == original_uuid
        assert response.json()["status"] == "pending_connection"

    def test_post__feature_flag_disabled__returns_403(
        self,
        admin_client: APIClient,
        warehouse_connection_url: str,
    ) -> None:
        # Given - no enable_features call

        # When
        response = admin_client.post(
            warehouse_connection_url,
            data={"warehouse_type": "flagsmith"},
            format="json",
        )

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post__non_admin__returns_403(
        self,
        staff_client: APIClient,
        environment: Environment,
        enable_features: EnableFeaturesFixture,
    ) -> None:
        # Given
        enable_features("experimentation_warehouse_connection")
        url = reverse_warehouse_connection_url(environment.api_key)

        # When
        response = staff_client.post(
            url,
            data={"warehouse_type": "flagsmith"},
            format="json",
        )

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post__creates_audit_log(
        self,
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
        assert AuditLog.objects.filter(
            related_object_type=RelatedObjectType.WAREHOUSE_CONNECTION.name,
        ).count() == 1
        audit_log = AuditLog.objects.get(
            related_object_type=RelatedObjectType.WAREHOUSE_CONNECTION.name,
        )
        assert "created" in audit_log.log
        assert environment.name in audit_log.log


class TestWarehouseConnectionViewGet:
    def test_get__exists__returns_200(
        self,
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
        assert data["warehouse_type"] == "flagsmith"
        assert data["status"] == "pending_connection"
        assert data["name"] == f"Flagsmith Warehouse - {environment.name}"
        assert data["uuid"] == str(warehouse_connection.uuid)
        assert "created_at" in data

    def test_get__not_exists__returns_404(
        self,
        admin_client: APIClient,
        enable_features: EnableFeaturesFixture,
        warehouse_connection_url: str,
    ) -> None:
        # Given
        enable_features("experimentation_warehouse_connection")

        # When
        response = admin_client.get(warehouse_connection_url)

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestWarehouseConnectionViewDelete:
    def test_delete__exists__returns_204(
        self,
        admin_client: APIClient,
        environment: Environment,
        enable_features: EnableFeaturesFixture,
        warehouse_connection: WarehouseConnection,
        warehouse_connection_url: str,
    ) -> None:
        # Given
        enable_features("experimentation_warehouse_connection")

        # When
        response = admin_client.delete(warehouse_connection_url)

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert WarehouseConnection.objects.filter(environment=environment).count() == 0
        deleted = WarehouseConnection.objects.all_with_deleted().get(
            pk=warehouse_connection.pk,
        )
        assert deleted.deleted_at is not None

    def test_delete__not_exists__returns_404(
        self,
        admin_client: APIClient,
        enable_features: EnableFeaturesFixture,
        warehouse_connection_url: str,
    ) -> None:
        # Given
        enable_features("experimentation_warehouse_connection")

        # When
        response = admin_client.delete(warehouse_connection_url)

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete__creates_audit_log(
        self,
        admin_client: APIClient,
        environment: Environment,
        enable_features: EnableFeaturesFixture,
        warehouse_connection: WarehouseConnection,
        warehouse_connection_url: str,
    ) -> None:
        # Given
        enable_features("experimentation_warehouse_connection")

        # When
        admin_client.delete(warehouse_connection_url)

        # Then
        assert AuditLog.objects.filter(
            related_object_type=RelatedObjectType.WAREHOUSE_CONNECTION.name,
        ).count() == 1
        audit_log = AuditLog.objects.get(
            related_object_type=RelatedObjectType.WAREHOUSE_CONNECTION.name,
        )
        assert "deleted" in audit_log.log
        assert environment.name in audit_log.log
