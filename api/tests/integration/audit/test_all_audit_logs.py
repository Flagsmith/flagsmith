from rest_framework.test import APIClient

from audit.models import AuditLog
from organisations.models import Organisation


def test_get_logs__mixed_direct_and_indirect_relation_to_organisation__responds_200_with_all_logs(
    admin_client: APIClient,
    environment: int,
    organisation: int,
    project: int,
) -> None:
    # Given
    AuditLog.objects.create(
        organisation_id=organisation,
        log="User `alice@example.com` joined the organisation",
    )
    AuditLog.objects.create(project_id=project, log="Flag `squeeze` created")
    AuditLog.objects.create(environment_id=environment, log="Flag `squeeze` enabled")

    # When
    response = admin_client.get("/api/v1/audit/")

    # Then
    assert response.status_code == 200
    assert [result["log"] for result in response.json()["results"]] == [
        "Flag `squeeze` enabled",
        "Flag `squeeze` created",
        "User `alice@example.com` joined the organisation",
        "New Environment created: Test Environment",
    ]


def test_get_logs__multiple_organisations__responds_200_with_all_logs(
    admin_client: APIClient,
    organisation: int,
) -> None:
    # Given
    other_organisation = admin_client.post(
        "/api/v1/organisations/", {"name": "Bananas Inc"}
    ).json()["id"]
    AuditLog.objects.create(
        organisation_id=organisation,
        log="User `alice@example.com` joined the organisation",
    )
    AuditLog.objects.create(
        organisation_id=other_organisation,
        log="User `bob@example.com` joined the organisation",
    )

    # When
    response = admin_client.get("/api/v1/audit/")

    # Then
    assert response.status_code == 200
    assert [result["log"] for result in response.json()["results"]] == [
        "User `bob@example.com` joined the organisation",
        "User `alice@example.com` joined the organisation",
    ]


def test_get_logs__unrelated_organisation__responds_200_with_logs_from_organisations_user_is_related_to(
    admin_client: APIClient,
    organisation: int,
) -> None:
    # Given
    unrelated_organisation = Organisation.objects.create(name="Bananas Inc")
    AuditLog.objects.create(
        organisation_id=organisation,
        log="User `alice@example.com` joined the organisation",
    )
    AuditLog.objects.create(
        organisation=unrelated_organisation,
        log="User `bob@example.com` joined the organisation",
    )

    # When
    response = admin_client.get("/api/v1/audit/")

    # Then
    assert response.status_code == 200
    assert [result["log"] for result in response.json()["results"]] == [
        "User `alice@example.com` joined the organisation",
    ]


def test_get_logs__organisation_filter__responds_200_with_only_logs_for_that_organisation(
    admin_client: APIClient,
    organisation: int,
    project: int,
) -> None:
    # Given
    other_organisation = admin_client.post(
        "/api/v1/organisations/", {"name": "Bananas Inc"}
    ).json()["id"]
    AuditLog.objects.create(
        organisation_id=organisation,
        log="User `alice@example.com` joined the organisation",
    )
    AuditLog.objects.create(project_id=project, log="Flag `squeeze` created")
    AuditLog.objects.create(
        organisation_id=other_organisation,
        log="User `bob@example.com` joined the organisation",
    )

    # When
    response = admin_client.get("/api/v1/audit/", {"organisation": organisation})

    # Then
    assert response.status_code == 200
    assert [result["log"] for result in response.json()["results"]] == [
        "Flag `squeeze` created",
        "User `alice@example.com` joined the organisation",
    ]


def test_get_logs__non_admin_user__responds_200_with_no_logs(
    non_admin_client: APIClient,
    organisation: int,
    project: int,
) -> None:
    # Given
    AuditLog.objects.create(
        organisation_id=organisation,
        log="User `alice@example.com` joined the organisation",
    )
    AuditLog.objects.create(project_id=project, log="Flag `squeeze` created")

    # When
    response = non_admin_client.get("/api/v1/audit/")

    # Then
    assert response.status_code == 200
    assert response.json()["results"] == []
