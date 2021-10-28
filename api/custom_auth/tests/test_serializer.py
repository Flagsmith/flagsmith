from custom_auth.serializers import CustomUserCreateSerializer
from users.models import FFAdminUser

user_dict = {
    "email": "TestUser@mail.com",
    "password": "pass@word123",
    "first_name": "test",
    "last_name": "user",
}


def test_CustomUserCreateSerializer_converts_email_to_lower_case(db):
    # Given
    serializer = CustomUserCreateSerializer(data=user_dict)
    # When
    serializer.is_valid(raise_exception=True)
    # Then
    assert serializer.validated_data["email"] == "testuser@mail.com"


def test_CustomUserCreateSerializer_does_case_insensitive_lookup_with_email(db):

    # Given
    FFAdminUser.objects.create(email="testuser@mail.com")
    serializer = CustomUserCreateSerializer(data=user_dict)

    # When
    assert serializer.is_valid() is False
    assert (
        serializer.errors["email"][0].title()
        == "Feature Flag Admin User With This Email Already Exists."
    )
