import socket

import pytest
from django.core.exceptions import ValidationError
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from core.validators import validate_no_internal_address


@pytest.mark.parametrize(
    "url, allowed_host",
    [
        ("http://hooks.internal.example.com/", "hooks.internal.example.com"),
        ("http://hooks.internal.example.com/", ".internal.example.com"),
        ("http://hooks.internal.example.com/", "*.internal.example.com"),
        ("http://10.0.0.5/", "10.0.0.5"),
        ("http://[fd00::1]/", "[fd00::1]"),
        ("http://127.0.0.1/", "*"),
    ],
)
def test_validate_no_internal_address__host_allowed__does_not_raise(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    url: str,
    allowed_host: str,
) -> None:
    # Given
    settings.SSRF_ALLOWED_HOSTS = [allowed_host]
    mocker.patch(
        "core.network.socket.getaddrinfo",
        return_value=[(socket.AF_INET, None, None, None, ("10.0.0.5", 0))],
    )

    # When / Then
    validate_no_internal_address(url)


@pytest.mark.parametrize("allowed_hosts", [[], ["other.example.com"]])
def test_validate_no_internal_address__host_not_allowed__raises_validation_error(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    allowed_hosts: list[str],
) -> None:
    # Given
    settings.SSRF_ALLOWED_HOSTS = allowed_hosts
    mocker.patch(
        "core.network.socket.getaddrinfo",
        return_value=[(socket.AF_INET, None, None, None, ("10.0.0.5", 0))],
    )

    # When
    with pytest.raises(ValidationError) as exc_info:
        validate_no_internal_address("http://hooks.internal.example.com/")

    # Then
    assert exc_info.value.code == "internal_address"
