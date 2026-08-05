import socket
from unittest import mock

import pytest
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from organisations.models import Organisation
from organisations.serializers import (
    OrganisationWebhookSerializer,
    UpdateSubscriptionSerializer,
)


def test_update_subscription_serializer__create__updates_subscription(
    organisation: Organisation,
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.ENABLE_CHARGEBEE = True
    subscription_data = {
        "subscription_id": "new-sub-id",
        "plan": "startup-v2",
        "max_seats": 10,
        "max_api_calls": 1000000,
        "customer_id": "cust-123",
        "payment_method": "CHARGEBEE",
    }
    mocker.patch(
        "organisations.serializers.get_subscription_data_from_hosted_page",
        return_value=subscription_data,
    )

    serializer = UpdateSubscriptionSerializer(
        data={"hosted_page_id": "hp-123"},
        context={"organisation": organisation.id},
    )
    serializer.is_valid(raise_exception=True)

    # When
    result = serializer.save()

    # Then
    assert result == organisation
    organisation.subscription.refresh_from_db()
    assert organisation.subscription.subscription_id == "new-sub-id"
    assert organisation.subscription.plan == "startup-v2"


def test_organisation_webhook_serializer__private_ip__is_invalid() -> None:
    # Given
    serializer = OrganisationWebhookSerializer(data={"url": "http://127.0.0.1/hook"})

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid is False
    assert "internal_address" in str(serializer.errors["url"])


def test_organisation_webhook_serializer__hostname_resolving_to_private_ip__is_invalid() -> (  # noqa: E501
    None
):
    # Given — a hostname that resolves to an RFC1918 address
    serializer = OrganisationWebhookSerializer(
        data={"url": "http://internal.example.com/hook"}
    )

    # When
    with mock.patch(
        "core.network.socket.getaddrinfo",
        return_value=[(socket.AF_INET, None, None, None, ("10.0.0.5", 0))],
    ):
        is_valid = serializer.is_valid()

    # Then
    assert is_valid is False
    assert "internal_address" in str(serializer.errors["url"])


def test_organisation_webhook_serializer__non_http_scheme__is_invalid() -> None:
    # Given
    serializer = OrganisationWebhookSerializer(data={"url": "ftp://example.com/hook"})

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid is False
    assert "url" in serializer.errors


@pytest.mark.parametrize(
    "url",
    ["https://example.com/hook", "http://8.8.8.8/hook"],
)
def test_organisation_webhook_serializer__public_url__is_valid(url: str) -> None:
    # Given
    serializer = OrganisationWebhookSerializer(data={"url": url})

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid is True
