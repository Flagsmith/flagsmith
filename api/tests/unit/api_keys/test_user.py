import pytest
from pytest_lazyfixture import lazy_fixture

from api_keys.user import APIKeyUser


def test__is_authenticated(master_api_key):
    # Given
    user = APIKeyUser(master_api_key)

    # Then
    assert user.is_authenticated() is True


@pytest.mark.parametrize(
    "org, expected_result",
    [
        (lazy_fixture("organisation"), True),
        (lazy_fixture("organisation_two"), False),
    ],
)
def test__belongs_to(org, expected_result, master_api_key):
    # Given
    user = APIKeyUser(master_api_key)

    # Then
    assert user.belongs_to(org.id) == expected_result
