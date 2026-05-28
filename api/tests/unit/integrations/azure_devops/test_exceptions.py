import pytest

from integrations.azure_devops.client.exceptions import (
    AzureDevOpsAuthError,
    AzureDevOpsError,
    AzureDevOpsNotFoundError,
)


def test_azure_devops_auth_error__inheritance__is_subclass_of_base() -> None:
    # Given
    cls = AzureDevOpsAuthError

    # When
    is_subclass = issubclass(cls, AzureDevOpsError)

    # Then
    assert is_subclass


def test_azure_devops_not_found_error__inheritance__is_subclass_of_base() -> None:
    # Given
    cls = AzureDevOpsNotFoundError

    # When
    is_subclass = issubclass(cls, AzureDevOpsError)

    # Then
    assert is_subclass


def test_azure_devops_error__base__is_exception_subclass() -> None:
    # Given
    cls = AzureDevOpsError

    # When
    is_exception = issubclass(cls, Exception)

    # Then
    assert is_exception


def test_azure_devops_auth_error__raise_and_catch__as_base_works() -> None:
    # Given
    def raise_auth_error() -> None:
        raise AzureDevOpsAuthError("invalid PAT")

    # When
    with pytest.raises(AzureDevOpsError) as exc_info:
        raise_auth_error()

    # Then
    assert "invalid PAT" in str(exc_info.value)
