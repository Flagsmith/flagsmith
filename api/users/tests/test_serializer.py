import pytest
from rest_framework.exceptions import ValidationError

from users.serializers import UserIdsSerializer


def test_user_ids_serializer_raises_exception_for_invalid_user_id(db):
    # Given
    serializer = UserIdsSerializer(data={"user_ids": [99999]})

    # Then
    with pytest.raises(ValidationError):
        serializer.is_valid(raise_exception=True)
