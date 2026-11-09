import json
from unittest import mock

import pytest
import responses
from pytest_django import DjangoAssertNumQueries
from rest_framework.test import APIClient

from audit.models import AuditLog
from environments.models import Environment
from organisations.models import Organisation
from projects.models import Project
from users.models import FFAdminUser


@pytest.fixture
def project(organisation: int) -> int:
    """Create a project outside the API, so it records no audit log."""
    return Project.objects.create(  # type: ignore[no-any-return]  # Removable once django-softdelete is typed
        name="Orangify website", organisation_id=organisation
    ).id


@pytest.fixture
def environment(project: int) -> int:
    """Create an environment outside the API, so it records no audit log."""
    return Environment.objects.create(  # type: ignore[no-any-return]  # Removable once django-softdelete is typed
        name="Production", project_id=project
    ).id


def test_get_logs__logs_directly_associated_with_organisation__responds_200_with_them(
    admin_client: APIClient,
    organisation: int,
) -> None:
    # Given
    other_organisation = Organisation.objects.create(name="Bananas Inc")
    AuditLog.objects.create(
        organisation_id=other_organisation.id,
        log="User `bob@example.com` joined the organisation",
    )
    audit_log = AuditLog.objects.create(
        organisation_id=organisation,
        log="User `alice@example.com` joined the organisation",
    )

    # When
    response = admin_client.get(f"/api/v1/organisations/{organisation}/audit/")

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": audit_log.id,
                "created_date": mock.ANY,
                "log": "User `alice@example.com` joined the organisation",
                "author": None,
                "organisation": {"id": organisation, "name": "Test org"},
                "environment": None,
                "project": None,
                "related_object_id": None,
                "related_object_uuid": None,
                "related_object_type": None,
                "is_system_event": False,
            }
        ],
    }


def test_get_logs__logs_indirectly_associated_with_organisation__responds_200_with_them(
    admin_client: APIClient,
    environment: int,
    organisation: int,
    project: int,
) -> None:
    # Given
    other_organisation = Organisation.objects.create(name="Bananas Inc")
    other_project = Project.objects.create(
        name="Winged Bananas Website", organisation=other_organisation
    )
    AuditLog.objects.create(project=other_project, log="Flag `peel` created")
    AuditLog.objects.create(project_id=project, log="Flag `squeeze` created")
    AuditLog.objects.create(environment_id=environment, log="Flag `squeeze` enabled")

    # When
    response = admin_client.get(f"/api/v1/organisations/{organisation}/audit/")

    # Then
    assert response.status_code == 200
    assert [result["log"] for result in response.json()["results"]] == [
        "Flag `squeeze` enabled",
        "Flag `squeeze` created",
    ]


@pytest.mark.parametrize(
    ["filter_args", "expected"],
    [
        (
            {"project": "project"},
            [
                "Flag `squeeze` enabled",
                "Project `Orangify website` created",
            ],
        ),
        (
            {"environments": "environment"},
            [
                "Flag `squeeze` enabled",
            ],
        ),
        (
            {"project": "project", "environments": "environment"},
            [
                "Flag `squeeze` enabled",
            ],
        ),
    ],
)
def test_get_logs__mixed_logs_with_filter__responds_200_with_filtered_logs(
    admin_client: APIClient,
    environment: int,
    expected: list[str],
    filter_args: dict[str, str],
    organisation: int,
    project: int,
    request: pytest.FixtureRequest,
) -> None:
    # Given
    AuditLog.objects.create(
        organisation_id=organisation,
        log="User `alice@example.com` joined the organisation",
    )
    AuditLog.objects.create(
        project_id=project,
        log="Project `Orangify website` created",
    )
    AuditLog.objects.create(
        environment_id=environment,
        log="Flag `squeeze` enabled",
    )

    # When
    response = admin_client.get(
        f"/api/v1/organisations/{organisation}/audit/",
        {name: request.getfixturevalue(value) for name, value in filter_args.items()},
    )

    # Then
    assert response.status_code == 200
    assert [result["log"] for result in response.json()["results"]] == expected


@pytest.mark.parametrize(
    ["is_organisation_level", "expected"],
    [
        (
            True,
            [
                "User `alice@example.com` joined the organisation",
            ],
        ),
        (
            False,
            [
                "Flag `squeeze` enabled",
                "Project `Orangify website` created",
            ],
        ),
    ],
)
def test_get_logs__mixed_logs_filtered_by_is_organisation_level__responds_200_with_filtered_logs(
    admin_client: APIClient,
    environment: int,
    expected: list[str],
    is_organisation_level: bool,
    organisation: int,
    project: int,
) -> None:
    # Given
    AuditLog.objects.create(
        organisation_id=organisation,
        log="User `alice@example.com` joined the organisation",
    )
    AuditLog.objects.create(
        project_id=project,
        log="Project `Orangify website` created",
    )
    AuditLog.objects.create(
        environment_id=environment,
        log="Flag `squeeze` enabled",
    )

    # When
    response = admin_client.get(
        f"/api/v1/organisations/{organisation}/audit/",
        {"is_organisation_level": is_organisation_level},
    )

    # Then
    assert response.status_code == 200
    assert [result["log"] for result in response.json()["results"]] == expected


@pytest.mark.parametrize(
    "filter_args",
    [
        {"project": "project"},
        {"environments": "environment"},
        {"project": "project", "environments": "environment"},
    ],
)
def test_get_logs__filters_by_both_is_organisation_level_and_project_or_environment__responds_400(
    admin_client: APIClient,
    environment: int,
    filter_args: dict[str, str],
    organisation: int,
    project: int,
    request: pytest.FixtureRequest,
) -> None:
    # Given / When
    response = admin_client.get(
        f"/api/v1/organisations/{organisation}/audit/",
        {
            "is_organisation_level": True,
            **{
                name: request.getfixturevalue(value)
                for name, value in filter_args.items()
            },
        },
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "non_field_errors": [
            "Organisation-level logs cannot be filtered by project or environment."
        ]
    }


def test_get_logs__mixed_logs__makes_expected_queries(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    django_assert_num_queries: DjangoAssertNumQueries,
    environment: int,
    organisation: int,
    project: int,
) -> None:
    # Given
    AuditLog.objects.create(
        organisation_id=organisation,
        author=admin_user,
        log="User `alice@example.com` joined the organisation",
    )
    AuditLog.objects.create(
        organisation_id=organisation,
        author=admin_user,
        log="User `bob@example.com` joined the organisation",
    )
    AuditLog.objects.create(
        project_id=project,
        author=admin_user,
        log="Flag `squeeze` created",
    )
    AuditLog.objects.create(
        project_id=project,
        author=admin_user,
        log="Flag `peel` created",
    )
    AuditLog.objects.create(
        environment_id=environment,
        author=admin_user,
        log="Flag `squeeze` enabled",
    )
    AuditLog.objects.create(
        environment_id=environment,
        author=admin_user,
        log="Flag `peel` enabled",
    )

    # When
    with django_assert_num_queries(5):
        response = admin_client.get(f"/api/v1/organisations/{organisation}/audit/")

    # Then
    assert response.status_code == 200


def test_get_logs__member_but_not_admin__responds_403(
    non_admin_client: APIClient,
    organisation: int,
) -> None:
    # Given / When
    response = non_admin_client.get(f"/api/v1/organisations/{organisation}/audit/")

    # Then
    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to perform this action."
    }


def test_get_logs__non_member__responds_404(
    organisation: int,
    staff_client: APIClient,
) -> None:
    # Given / When
    response = staff_client.get(f"/api/v1/organisations/{organisation}/audit/")

    # Then
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found."}


@responses.activate
def test_webhook_dispatch__organisation_log__sends_webhook(
    admin_client: APIClient,
    organisation: int,
) -> None:
    # Given
    admin_client.post(
        f"/api/v1/organisations/{organisation}/webhooks/",
        {"url": "https://example.com/audit-hook", "enabled": True},
        format="json",
    )
    responses.post("https://example.com/audit-hook", status=200)

    # When
    audit_log = AuditLog.objects.create(
        organisation_id=organisation,
        log="User `alice@example.com` joined the organisation",
    )

    # Then
    [webhook_call] = responses.calls
    assert json.loads(webhook_call.request.body) == {
        "event_type": "AUDIT_LOG_CREATED",
        "data": {
            "id": audit_log.id,
            "created_date": mock.ANY,
            "log": "User `alice@example.com` joined the organisation",
            "author": None,
            "organisation": {"id": organisation, "name": "Test org"},
            "environment": None,
            "project": None,
            "related_object_id": None,
            "related_object_uuid": None,
            "related_object_type": None,
            "is_system_event": False,
        },
    }
