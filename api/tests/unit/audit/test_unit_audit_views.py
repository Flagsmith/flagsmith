import typing
from datetime import timedelta

import pytest
from django.db.models import Model
from django.urls import reverse
from django.utils import timezone
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from audit.constants import ENVIRONMENT_FEATURE_VERSION_PUBLISHED_MESSAGE
from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from environments.models import Environment
from features.models import Feature
from features.versioning.models import EnvironmentFeatureVersion
from organisations.models import Organisation, OrganisationRole
from organisations.subscriptions.metadata import BaseSubscriptionMetadata
from projects.models import Project
from users.models import FFAdminUser


@pytest.fixture(autouse=True)
def subscription_metadata(mocker: MockerFixture) -> None:
    metadata = BaseSubscriptionMetadata(
        audit_log_visibility_days=None,
    )
    mocker.patch(
        "organisations.models.Subscription.get_subscription_metadata",
        return_value=metadata,
    )
    return metadata


def test_audit_log_can_be_filtered_by_environments(
    admin_client: APIClient, project: Project, environment: Environment
) -> None:
    # Given
    audit_env = Environment.objects.create(name="env_n", project=project)

    AuditLog.objects.create(project=project)
    AuditLog.objects.create(project=project, environment=environment)
    AuditLog.objects.create(project=project, environment=audit_env)

    url = reverse("api-v1:audit-list")
    # When
    response = admin_client.get(
        url, {"project": project.id, "environments": [audit_env.id]}
    )
    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["environment"]["id"] == audit_env.id


def test_audit_log_can_be_filtered_by_log_text(
    admin_client: APIClient, project: Project, environment: Environment
) -> None:
    # Given
    flag_state_updated_log = "Flag state updated"
    flag_state_deleted_log = "flag state deleted"

    AuditLog.objects.create(project=project, log="New flag created")
    AuditLog.objects.create(project=project, log=flag_state_updated_log)
    AuditLog.objects.create(project=project, log=flag_state_deleted_log)
    AuditLog.objects.create(project=project, log="New Environment Created")

    url = reverse("api-v1:audit-list")

    # When
    response = admin_client.get(url, {"project": project.id, "search": "flag state"})

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"][0]["log"] == flag_state_deleted_log
    assert response.json()["results"][1]["log"] == flag_state_updated_log


def test_audit_log_can_be_filtered_by_project(
    admin_client: APIClient,
    project: Project,
    environment: Environment,
    organisation: Organisation,
) -> None:
    # Given
    another_project = Project.objects.create(
        name="another_project", organisation=organisation
    )
    AuditLog.objects.create(project=project)
    AuditLog.objects.create(project=project, environment=environment)
    AuditLog.objects.create(project=another_project)

    url = reverse("api-v1:audit-list")

    # When
    response = admin_client.get(url, {"project": project.id})

    # Then
    assert response.json()["count"] == 2
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"][0]["project"]["id"] == project.id
    assert response.json()["results"][1]["project"]["id"] == project.id


def test_audit_log_can_be_filtered_by_is_system_event(
    admin_client: APIClient,
    project: Project,
    environment: Environment,
    organisation: Organisation,
) -> None:
    # Given
    AuditLog.objects.create(project=project, is_system_event=True)
    AuditLog.objects.create(
        project=project, environment=environment, is_system_event=False
    )

    url = reverse("api-v1:audit-list")

    # When
    response = admin_client.get(url, {"is_system_event": True})

    # Then
    assert response.json()["count"] == 1
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"][0]["is_system_event"] is True


def test_regular_user_cannot_list_audit_log(
    project: Project,
    environment: Environment,
    organisation: Organisation,
    django_user_model: typing.Type[Model],
    api_client: APIClient,
) -> None:
    # Given
    AuditLog.objects.create(environment=environment)
    url = reverse("api-v1:audit-list")
    user = django_user_model.objects.create(email="test@example.com")
    user.add_organisation(organisation)
    api_client.force_authenticate(user)

    # When
    response = api_client.get(url)

    # Then
    assert response.json()["count"] == 0


def test_admin_user_cannot_list_audit_log_of_another_organisation(
    api_client: APIClient,
    organisation: Organisation,
    project: Project,
    django_user_model: typing.Type[Model],
) -> None:
    # Given
    another_organisation = Organisation.objects.create(name="another organisation")
    user = django_user_model.objects.create(email="test@example.com")
    user.add_organisation(another_organisation, role=OrganisationRole.ADMIN)

    AuditLog.objects.create(project=project)
    url = reverse("api-v1:audit-list")

    api_client.force_authenticate(user)

    # When
    response = api_client.get(url)

    # Then
    assert response.json()["count"] == 0


def test_retrieve_environment_feature_version_published_audit_log_record_includes_required_fields(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    environment_v2_versioning: Environment,
    feature: Feature,
) -> None:
    # Given
    new_version = EnvironmentFeatureVersion.objects.create(
        feature=feature,
        environment=environment_v2_versioning,
    )
    new_version.publish(published_by=admin_user)

    audit_log = (
        AuditLog.objects.filter(related_object_type=RelatedObjectType.EF_VERSION.name)
        .order_by("-created_date")
        .first()
    )
    url = reverse("api-v1:audit-detail", args=[audit_log.id])

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["related_object_uuid"] == str(new_version.uuid)
    assert response_json["related_object_type"] == RelatedObjectType.EF_VERSION.name
    assert (
        response_json["log"]
        == ENVIRONMENT_FEATURE_VERSION_PUBLISHED_MESSAGE % feature.name
    )


def test_list_audit_log_for_project_limits_logs_returned_for_non_enterprise(
    subscription_metadata: BaseSubscriptionMetadata,
    project: Project,
    admin_client: APIClient,
) -> None:
    # Given
    url = reverse("api-v1:projects:project-audit-list", args=[project.id])

    subscription_metadata.audit_log_visibility_days = 1

    now = timezone.now()
    two_days_ago = now - timedelta(days=2)

    AuditLog.objects.create(
        project=project, log="Something that happened today", created_date=now
    )
    AuditLog.objects.create(
        project=project,
        log="Something that happened 2 days ago",
        created_date=two_days_ago,
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 1
    assert response_json["results"][0]["log"] == "Something that happened today"


def test_list_audit_log_for_organisation_limits_logs_returned_for_non_enterprise(
    subscription_metadata: BaseSubscriptionMetadata,
    organisation: Organisation,
    project: Project,
    admin_client: APIClient,
) -> None:
    # Given
    url = reverse("api-v1:organisations:audit-log-list", args=[organisation.id])

    subscription_metadata.audit_log_visibility_days = 1

    now = timezone.now()
    two_days_ago = now - timedelta(days=2)

    AuditLog.objects.create(
        project=project, log="Something that happened today", created_date=now
    )
    AuditLog.objects.create(
        project=project,
        log="Something that happened 2 days ago",
        created_date=two_days_ago,
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 1
    assert response_json["results"][0]["log"] == "Something that happened today"
