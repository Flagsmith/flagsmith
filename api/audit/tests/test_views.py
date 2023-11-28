import typing

from django.db.models import Model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from audit.models import AuditLog
from environments.models import Environment
from organisations.models import Organisation, OrganisationRole
from projects.models import Project


def test_audit_log_can_be_filtered_by_environments(
    admin_client, organisation, project, environment
):
    # Given
    audit_env = Environment.objects.create(name="env_n", project=project)

    # new-style logs with organisation derived on creation
    AuditLog.objects.create(project=project)
    AuditLog.objects.create(project=project, environment=environment)
    # old-style project-only log
    pre_migration_log = AuditLog.objects.create(project=project, environment=audit_env)
    pre_migration_log._organisation = None
    pre_migration_log.save()
    assert not AuditLog.objects.get(pk=pre_migration_log.pk)._organisation_id

    url = reverse("api-v1:audit-list")
    # When
    response = admin_client.get(
        url, {"project": project.id, "environments": [audit_env.id]}
    )
    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] == 1
    assert data["results"][0]["organisation"]["id"] == organisation.pk
    assert data["results"][0]["project"]["id"] == project.pk
    assert data["results"][0]["environment"]["id"] == audit_env.pk


def test_audit_log_can_be_filtered_by_log_text(
    admin_client, organisation, project, environment
):
    # Given
    flag_state_updated_log = "Flag state updated"
    flag_state_deleted_log = "flag state deleted"

    # new-style logs with organisation derived on creation
    AuditLog.objects.create(project=project, log="New flag created")
    AuditLog.objects.create(project=project, log=flag_state_updated_log)
    AuditLog.objects.create(project=project, log=flag_state_deleted_log)
    AuditLog.objects.create(project=project, log="New Environment Created")

    url = reverse("api-v1:audit-list")

    # When
    response = admin_client.get(url, {"project": project.id, "search": "flag state"})

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] == 2
    # results are in reverse order of creation
    assert data["results"][0]["organisation"]["id"] == organisation.pk
    assert data["results"][0]["log"] == flag_state_deleted_log
    assert data["results"][1]["organisation"]["id"] == organisation.pk
    assert data["results"][1]["log"] == flag_state_updated_log


def test_audit_log_can_be_filtered_by_project(
    admin_client, organisation, project, environment
):
    # Given
    another_project = Project.objects.create(
        name="another_project", organisation=organisation
    )
    # old-style project-only log
    pre_migration_log = AuditLog.objects.create(project=project)
    pre_migration_log._organisation = None
    pre_migration_log.save()
    assert not AuditLog.objects.get(pk=pre_migration_log.pk)._organisation_id
    # new-style logs with organisation derived on creation
    AuditLog.objects.create(project=project, environment=environment)
    AuditLog.objects.create(project=another_project)

    url = reverse("api-v1:audit-list")

    # When
    response = admin_client.get(url, {"project": project.id})

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] == 2
    # results are in reverse order of creation
    assert data["results"][0]["organisation"]["id"] == organisation.pk
    assert data["results"][0]["project"]["id"] == project.pk
    assert data["results"][0]["environment"]["id"] == environment.pk
    assert data["results"][1]["organisation"]["id"] == organisation.pk
    assert data["results"][1]["project"]["id"] == project.pk


def test_audit_log_can_be_filtered_by_organisation(
    admin_client, organisation, project, environment
):
    # Given
    another_project = Project.objects.create(
        name="another_project", organisation=organisation
    )

    # old-style project-only log
    pre_migration_log = AuditLog.objects.create(project=project)
    pre_migration_log._organisation = None
    pre_migration_log.save()
    assert not AuditLog.objects.get(pk=pre_migration_log.pk)._organisation_id
    # new-style logs with organisation derived on creation
    AuditLog.objects.create(environment=environment)
    AuditLog.objects.create(project=another_project)
    # new-style organisation-only log
    AuditLog.objects.create(organisation=organisation)

    url = reverse("api-v1:audit-list")

    # When
    response = admin_client.get(url, {"organisation": organisation.id})

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] == 4
    # results are in reverse order of creation
    assert data["results"][0]["organisation"]["id"] == organisation.pk
    assert not data["results"][0]["project"]
    assert not data["results"][0]["environment"]
    assert data["results"][1]["organisation"]["id"] == organisation.pk
    assert data["results"][1]["project"]["id"] == another_project.pk
    assert not data["results"][1]["environment"]
    assert data["results"][2]["organisation"]["id"] == organisation.pk
    assert data["results"][2]["project"]["id"] == project.pk
    assert data["results"][2]["environment"]["id"] == environment.pk
    assert data["results"][3]["organisation"]["id"] == organisation.pk
    assert data["results"][3]["project"]["id"] == project.pk
    assert not data["results"][3]["environment"]


def test_audit_log_can_be_filtered_by_is_system_event(
    admin_client, project, environment, organisation
):
    # Given
    AuditLog.objects.create(project=project, is_system_event=True)
    AuditLog.objects.create(
        project=project, environment=environment, is_system_event=False
    )

    url = reverse("api-v1:audit-list")

    # When
    response = admin_client.get(url, {"is_system_event": True})

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["is_system_event"] is True


def test_regular_user_cannot_list_audit_log(
    project: Project,
    environment: Environment,
    organisation: Organisation,
    django_user_model: typing.Type[Model],
    api_client: APIClient,
):
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
):
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
