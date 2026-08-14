from unittest.mock import Mock

import freezegun
import pytest
from django.utils import timezone
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture
from rest_framework.test import APIClient

from environments.models import Environment

pytestmark = pytest.mark.freeze_time("2077-07-07T07:07:07Z")


@pytest.fixture
def onboarded_environment(environment: Environment) -> Environment:
    environment.first_evaluated_at = timezone.now()
    environment.first_evaluated_sdk_label = "flagsmith-python-sdk"
    environment.save(update_fields=["first_evaluated_at", "first_evaluated_sdk_label"])
    return environment


@pytest.fixture(autouse=True)
def write_environment_documents(mocker: MockerFixture) -> Mock:
    return mocker.patch.object(Environment, "write_environment_documents")


def test_get_onboarding_status__never_evaluated__responds_200(
    api_client: APIClient,
    environment: Environment,
) -> None:
    # Given / When
    response = api_client.get(
        f"/api/v1/environments/{environment.api_key}/onboarding-status/"
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "first_evaluated_at": None,
        "first_evaluated_sdk_label": None,
    }


def test_get_onboarding_status__evaluated__responds_200(
    api_client: APIClient,
    onboarded_environment: Environment,
) -> None:
    # Given / When
    response = api_client.get(
        f"/api/v1/environments/{onboarded_environment.api_key}/onboarding-status/"
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "first_evaluated_at": "2077-07-07T07:07:07Z",
        "first_evaluated_sdk_label": "flagsmith-python-sdk",
    }


@pytest.mark.django_db
def test_get_onboarding_status__unknown_environment__responds_404(
    api_client: APIClient,
) -> None:
    # Given / When
    response = api_client.get("/api/v1/environments/unknown-api-key/onboarding-status/")

    # Then
    assert response.status_code == 404


def test_put_onboarding_status__never_evaluated__updates_environment(
    api_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    assert environment.first_evaluated_at is None
    assert environment.first_evaluated_sdk_label is None

    # When
    response = api_client.put(
        f"/api/v1/environments/{environment.api_key}/onboarding-status/",
        data={
            "first_evaluated_sdk_label": "flagsmith-python-sdk",
        },
        format="json",
    )

    # Then
    assert response.status_code == 204
    environment.refresh_from_db()
    assert environment.first_evaluated_at == timezone.now()
    assert environment.first_evaluated_sdk_label == "flagsmith-python-sdk"


def test_put_onboarding_status__evaluated__does_not_update_environment(
    api_client: APIClient,
    onboarded_environment: Environment,
) -> None:
    # Given
    assert onboarded_environment.first_evaluated_at is not None
    assert onboarded_environment.first_evaluated_sdk_label is not None

    # When
    with freezegun.freeze_time("2088-08-08T08:08:08Z"):
        response = api_client.put(
            f"/api/v1/environments/{onboarded_environment.api_key}/onboarding-status/",
            data={
                "first_evaluated_sdk_label": "flagsmith-php-sdk",
            },
            format="json",
        )

    # Then
    assert response.status_code == 204
    onboarded_environment.refresh_from_db()
    assert "2077" in onboarded_environment.first_evaluated_at.isoformat()
    assert "python" in onboarded_environment.first_evaluated_sdk_label


def test_put_onboarding_status__never_evaluated__writes_environment_document(
    api_client: APIClient,
    environment: Environment,
    write_environment_documents: Mock,
) -> None:
    # Given / When
    response = api_client.put(
        f"/api/v1/environments/{environment.api_key}/onboarding-status/",
        data={
            "first_evaluated_sdk_label": "flagsmith-python-sdk",
        },
        format="json",
    )

    # Then
    assert response.status_code == 204
    write_environment_documents.assert_called_once_with(environment_id=environment.id)


def test_put_onboarding_status__evaluated__skips_environment_document(
    api_client: APIClient,
    onboarded_environment: Environment,
    write_environment_documents: Mock,
) -> None:
    # Given / When
    response = api_client.put(
        f"/api/v1/environments/{onboarded_environment.api_key}/onboarding-status/",
        data={
            "first_evaluated_sdk_label": "flagsmith-python-sdk",
        },
        format="json",
    )

    # Then
    assert response.status_code == 204
    write_environment_documents.assert_not_called()


def test_put_onboarding_status__never_evaluated__logs_first_evaluation(
    api_client: APIClient,
    environment: Environment,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = api_client.put(
        f"/api/v1/environments/{environment.api_key}/onboarding-status/",
        data={
            "first_evaluated_sdk_label": "flagsmith-python-sdk",
        },
        format="json",
    )

    # Then
    assert response.status_code == 204
    assert log.has(
        "environment.first_evaluated",
        level="info",
        environment__id=environment.id,
        project__id=environment.project_id,
        organisation__id=environment.project.organisation_id,
        sdk__label="flagsmith-python-sdk",
    )


def test_put_onboarding_status__evaluated__logs_already_evaluated(
    api_client: APIClient,
    onboarded_environment: Environment,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = api_client.put(
        f"/api/v1/environments/{onboarded_environment.api_key}/onboarding-status/",
        data={
            "first_evaluated_sdk_label": "flagsmith-php-sdk",
        },
        format="json",
    )

    # Then
    assert response.status_code == 204
    assert log.has(
        "environment.already_evaluated",
        level="info",
        environment__id=onboarded_environment.id,
        project__id=onboarded_environment.project_id,
        organisation__id=onboarded_environment.project.organisation_id,
        sdk__label="flagsmith-php-sdk",
    )
    assert not log.has("environment.first_evaluated")


@pytest.mark.django_db
def test_put_onboarding_status__unknown_environment__responds_404(
    api_client: APIClient,
) -> None:
    # Given / When
    response = api_client.put(
        "/api/v1/environments/unknown-api-key/onboarding-status/",
        data={
            "first_evaluated_sdk_label": "flagsmith-python-sdk",
        },
        format="json",
    )

    # Then
    assert response.status_code == 404


def test_put_onboarding_status__invalid_sdk_label__responds_400(
    api_client: APIClient,
    environment: Environment,
) -> None:
    # Given / When
    response = api_client.put(
        f"/api/v1/environments/{environment.api_key}/onboarding-status/",
        data={
            "first_evaluated_sdk_label": "invalid-sdk-label",
        },
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "first_evaluated_sdk_label": ['"invalid-sdk-label" is not a valid choice.'],
    }
