from unittest.mock import MagicMock

import pytest
from rest_framework.exceptions import NotAuthenticated

from users.models import FFAdminUser
from users.serializers import CustomCurrentUserSerializer


class TestCustomCurrentUserSerializer:
    def test_to_representation_unauthenticated_user(self):
        # Given
        serializer = CustomCurrentUserSerializer()
        mock_user = MagicMock(spec=FFAdminUser)
        mock_user.is_authenticated = False

        # When/Then
        with pytest.raises(NotAuthenticated) as excinfo:
            serializer.to_representation(mock_user)

        assert str(excinfo.value) == "User is not authenticated."
        assert excinfo.value.detail == "User is not authenticated."
