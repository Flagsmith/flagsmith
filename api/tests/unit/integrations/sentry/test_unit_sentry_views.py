from typing import Any

import pytest
from rest_framework.test import APIClient

from environments.models import Environment
from integrations.sentry.models import SentryChangeTrackingConfiguration


def test_sentry__change_tracking__setup__accepts_new_configuration(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    pass

    # When
    url = f"/api/v1/environments/{environment.api_key}/integrations/sentry/"
    payload = {
        "webhook_url": "https://sentry.example.com/webhook",
        "secret": "hush hush!",
    }
    response = admin_client.post(url, payload, format="json")

    # Then
    assert response.status_code == 201
    assert (
        SentryChangeTrackingConfiguration.objects.filter(
            environment=environment,
            webhook_url="https://sentry.example.com/webhook",
            secret="hush hush!",
        ).count()
        == 1
    )


@pytest.mark.parametrize(
    "payload, errors",
    [
        (
            {
                "secret": "hush hush!",
            },
            {
                "webhook_url": ["This field is required."],
            },
        ),
        (
            {
                "webhook_url": "https://sentry.example.com/webhook",
            },
            {
                "secret": ["This field is required."],
            },
        ),
        (
            {
                "webhook_url": "https://sentry.example.com/webhook",
                "secret": "hush!",
            },
            {
                "secret": ["Ensure this field has at least 10 characters."],
            },
        ),
        (
            {
                "webhook_url": "https://sentry.example.com/webhook",
                "secret": "Hush, hush, hush, hush; I've already spoken, our love is broken; Baby, hush, hush",
            },
            {"secret": ["Ensure this field has no more than 60 characters."]},
        ),
        (
            {
                "webhook_url": "https://sentry.example.com/webhook",
                "secret": "Hush, hush, hush, hush; I've already spoken, our love is broken; Baby, hush, hush",
            },
            {"secret": ["Ensure this field has no more than 60 characters."]},
        ),
        (
            {
                "webhook_url": "https://sentry.example.com/webhook",
                "secret": "hush hush!",
            },
            ["This integration already exists for this environment."],
        ),
    ],
)
def test_sentry__change_tracking__setup__rejects_invalid_configuration(
    admin_client: APIClient,
    environment: Environment,
    errors: Any,
    payload: dict[str, str],
) -> None:
    # Given
    # Already existing configuration
    SentryChangeTrackingConfiguration.objects.create(
        environment=environment,
        webhook_url="https://sentry.example.com/webhook",
        secret="hush hush!",
    )

    # When
    url = f"/api/v1/environments/{environment.api_key}/integrations/sentry/"
    response = admin_client.post(url, payload, format="json")

    # Then
    assert response.status_code == 400
    assert response.json() == errors
