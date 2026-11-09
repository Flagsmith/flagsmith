from rest_framework.test import APIClient

from audit.models import AuditLog


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
