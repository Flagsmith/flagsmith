import pytest

from api_keys.models import MasterAPIKey
from core.dataclasses import AuthorData
from users.models import FFAdminUser


def test_author_data__user_and_api_key__raises_value_error() -> None:
    # Given / When / Then
    with pytest.raises(ValueError):
        AuthorData(user=FFAdminUser(), api_key=MasterAPIKey())
