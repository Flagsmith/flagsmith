from datetime import timedelta

import pytest
from common.environments.permissions import VIEW_ENVIRONMENT
from django.urls import reverse
from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment, EnvironmentAPIKey
from features.flag_bisect.models import (
    AgentMessage,
    Incident,
    IncidentState,
    SignalBucket,
    Suspect,
)
from features.models import Feature
from tests.types import WithEnvironmentPermissionsCallable

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def flag_bisect_enabled(settings: SettingsWrapper) -> None:
    settings.FLAG_BISECT_ENABLED = True


@pytest.fixture()
def incident(environment: Environment, feature: Feature) -> Incident:
    incident = Incident.objects.create(
        environment=environment,
        state=IncidentState.AWAITING_APPROVAL,
        onset_at=timezone.now() - timedelta(minutes=3),
        baseline_rate=0.01,
        regression_rate=0.09,
        beliefs=[[[], 0.1], [[str(feature.id)], 0.9]],
    )
    Suspect.objects.create(
        incident=incident,
        feature=feature,
        before_enabled=False,
        before_value=None,
        after_enabled=True,
        after_value=None,
        changed_at=timezone.now() - timedelta(minutes=5),
        prior=0.9,
    )
    AgentMessage.objects.create(incident=incident, agent="sentinel", text="Opened.")
    return incident


def _url(environment: Environment, name: str, *args: object) -> str:
    return reverse(
        f"api-v1:environments:flag-bisect:incidents-{name}",
        args=[environment.api_key, *args],
    )


def test_list_incidents__environment_admin__returns_incidents(
    admin_client_new: APIClient, environment: Environment, incident: Incident
) -> None:
    # Given / When
    response = admin_client_new.get(_url(environment, "list"))

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert [i["id"] for i in response.json()["results"]] == [incident.id]


def test_retrieve_incident__environment_admin__returns_suspects_hypotheses_and_trail(
    admin_client_new: APIClient,
    environment: Environment,
    incident: Incident,
    feature: Feature,
) -> None:
    # Given / When
    response = admin_client_new.get(_url(environment, "detail", incident.id))

    # Then
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["state"] == "AWAITING_APPROVAL"
    assert body["suspects"][0]["feature_name"] == feature.name
    assert body["suspects"][0]["posterior"] == pytest.approx(0.9)
    assert body["hypotheses"][0] == {
        "features": [feature.name],
        "probability": pytest.approx(0.9),
    }
    assert body["messages"] == [
        {
            "agent": "sentinel",
            "text": "Opened.",
            "created_at": body["messages"][0]["created_at"],
        }
    ]


def test_list_incidents__feature_disabled__is_forbidden(
    admin_client_new: APIClient, environment: Environment, settings: SettingsWrapper
) -> None:
    # Given
    settings.FLAG_BISECT_ENABLED = False

    # When
    response = admin_client_new.get(_url(environment, "list"))

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_incidents__not_an_environment_admin__is_forbidden(
    staff_client: APIClient,
    environment: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT], environment.id, False)

    # When
    response = staff_client.get(_url(environment, "list"))

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_incidents__unknown_environment__is_forbidden(
    admin_client_new: APIClient,
) -> None:
    # Given
    url = reverse("api-v1:environments:flag-bisect:incidents-list", args=["missing"])

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_approve_envelope__valid__creates_the_canary_and_starts_probing(
    admin_client_new: APIClient, environment: Environment, incident: Incident
) -> None:
    # Given / When
    response = admin_client_new.post(
        _url(environment, "approve-envelope", incident.id),
        {"canary_percent": 7},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["state"] == "PROBING"
    assert response.json()["canary_percent"] == 7
    assert response.json()["canary_segment"] is not None


def test_approve_envelope__canary_too_large__is_rejected(
    admin_client_new: APIClient, environment: Environment, incident: Incident
) -> None:
    # Given / When
    response = admin_client_new.post(
        _url(environment, "approve-envelope", incident.id),
        {"canary_percent": 50},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_abort__with_reason__stops_the_incident(
    admin_client_new: APIClient, environment: Environment, incident: Incident
) -> None:
    # Given / When
    short = admin_client_new.post(
        _url(environment, "abort", incident.id), {"reason": "no"}, format="json"
    )
    response = admin_client_new.post(
        _url(environment, "abort", incident.id),
        {"reason": "paging the team"},
        format="json",
    )

    # Then
    assert short.status_code == status.HTTP_400_BAD_REQUEST
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["state"] == "ABORTED"


def test_remediation__proposer_approves_own_proposal__is_refused(
    admin_client_new: APIClient,
    environment: Environment,
    incident: Incident,
    feature: Feature,
) -> None:
    # Given
    incident.state = IncidentState.IDENTIFIED
    incident.conclusion = {"ids": [str(feature.id)], "confidence": 0.99}
    incident.save()
    proposed = admin_client_new.post(
        _url(environment, "propose-remediation", incident.id)
    )

    # When
    response = admin_client_new.post(
        _url(environment, "approve-remediation", incident.id)
    )

    # Then
    assert proposed.status_code == status.HTTP_200_OK
    assert proposed.json()["state"] == "REMEDIATION_PROPOSED"
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_sdk_signals__server_key__records_the_outcomes(
    api_client: APIClient,
    environment: Environment,
    environment_api_key: EnvironmentAPIKey,
) -> None:
    # Given
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment_api_key.key)

    # When
    response = api_client.post(
        reverse("api-v1:flag-bisect-signals"),
        {
            "signals": [
                {"identifier": "a", "ok": True},
                {"identifier": "b", "ok": False},
            ]
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_202_ACCEPTED
    bucket = SignalBucket.objects.get(environment=environment)
    assert (bucket.total, bucket.failures) == (2, 1)


def test_sdk_signals__client_key__is_refused(
    api_client: APIClient, environment: Environment
) -> None:
    # Given
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    # When
    response = api_client.post(
        reverse("api-v1:flag-bisect-signals"),
        {"signals": [{"identifier": "a", "ok": True}]},
        format="json",
    )

    # Then
    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )
    assert not SignalBucket.objects.exists()


@pytest.mark.parametrize(
    "body", [{}, {"signals": []}, {"signals": [{"identifier": "a"}]}]
)
def test_sdk_signals__invalid_body__is_rejected(
    api_client: APIClient,
    environment_api_key: EnvironmentAPIKey,
    body: dict[str, object],
) -> None:
    # Given
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment_api_key.key)

    # When
    response = api_client.post(
        reverse("api-v1:flag-bisect-signals"), body, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_sdk_signals__feature_disabled__is_not_found(
    api_client: APIClient,
    environment_api_key: EnvironmentAPIKey,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.FLAG_BISECT_ENABLED = False
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment_api_key.key)

    # When
    response = api_client.post(
        reverse("api-v1:flag-bisect-signals"),
        {"signals": [{"identifier": "a", "ok": True}]},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_run_flag_bisect_swarm__disabled_or_enabled__runs_only_when_enabled(
    settings: SettingsWrapper, environment: Environment, mocker: MockerFixture
) -> None:
    # Given
    from features.flag_bisect import tasks

    run = mocker.patch("features.flag_bisect.tasks.services.run_swarm")

    # When
    settings.FLAG_BISECT_ENABLED = False
    tasks.run_flag_bisect_swarm()
    settings.FLAG_BISECT_ENABLED = True
    tasks.run_flag_bisect_swarm()

    # Then
    run.assert_called_once_with()
