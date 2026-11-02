import pytest

from experimentation.warehouses.base import is_disallowed_host


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
