from django.urls import reverse
from rest_framework import status

from audit.models import AuditLog
from environments.models import Environment


def test_audit_log_can_be_filtered_by_environments(admin_client, project, environment):
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
    assert response.json()["count"] == 2
    assert response.json()["results"][0]["environment"]["id"] == audit_env.id
    assert response.json()["results"][1]["environment"] is None


def test_audit_log_can_be_filtered_by_related_object_type(
    admin_client, project, environment
):
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
