from integrations.azure_devops.constants import (
    AZURE_DEVOPS_API_VERSION,
    AZURE_DEVOPS_CLIENT_TIMEOUT_SECONDS,
)


def test_constants__timeout__has_sensible_default() -> None:
    # Given
    timeout = AZURE_DEVOPS_CLIENT_TIMEOUT_SECONDS

    # When
    is_positive_int = isinstance(timeout, int) and timeout > 0

    # Then
    assert is_positive_int
    assert timeout <= 60


def test_constants__api_version__is_string() -> None:
    # Given
    version = AZURE_DEVOPS_API_VERSION

    # When
    is_string = isinstance(version, str)

    # Then
    assert is_string
    assert version
