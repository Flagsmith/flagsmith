import socket

import pytest
from pytest_mock import MockerFixture

from experimentation.warehouses.base import is_disallowed_host, pin_host_address
from experimentation.warehouses.exceptions import DeliveryConfigError


@pytest.mark.usefixtures("saas_mode")
def test_is_disallowed_host__internal_host_on_saas__returns_true() -> None:
    # Given
    host = "10.0.0.1"

    # When
    result = is_disallowed_host(host)

    # Then
    assert result is True


def test_is_disallowed_host__internal_host_on_self_hosted__returns_false() -> None:
    # Given
    host = "10.0.0.1"

    # When
    result = is_disallowed_host(host)

    # Then
    assert result is False


def _address_record(address: str) -> tuple[object, ...]:
    return (socket.AF_INET6, socket.SOCK_STREAM, 6, "", (address, 0))


@pytest.mark.usefixtures("saas_mode")
@pytest.mark.parametrize(
    "resolved, expected",
    [
        (["8.8.8.8", "2001:4860:4860::8888"], "8.8.8.8"),
        (
            ["8.8.8.8", "10.0.0.1"],
            "Host must not target internal or private network addresses.",
        ),
        (socket.gaierror("unresolvable"), "Could not connect to the host."),
    ],
    ids=["public", "public-and-internal", "unresolvable"],
)
def test_pin_host_address__saas__returns_checked_address_or_raises(
    mocker: MockerFixture,
    resolved: list[str] | Exception,
    expected: str,
) -> None:
    # Given
    mocker.patch(
        "core.network.socket.getaddrinfo",
        side_effect=resolved
        if isinstance(resolved, Exception)
        else lambda *_: [_address_record(address) for address in resolved],
    )

    # When
    try:
        result = pin_host_address("db.example.com")
    except DeliveryConfigError as error:
        result = str(error)

    # Then
    assert result == expected


def test_pin_host_address__self_hosted__returns_none(mocker: MockerFixture) -> None:
    # Given
    getaddrinfo = mocker.patch("core.network.socket.getaddrinfo")

    # When
    result = pin_host_address("db.internal")

    # Then
    assert result is None
    getaddrinfo.assert_not_called()
