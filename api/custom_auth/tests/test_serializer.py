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
    assert serializer.errors["detail"][0].title() == "Unable To Create Account"


def test_CustomUserCreateSerializer_calls_is_authentication_method_valid_correctly_if_auth_controller_is_installed(
    db, settings, mocker, rf
):

    # Given
    settings.AUTH_CONTROLLER_INSTALLED = True

    request = rf.post("/v1/auth/login")
    mocked_auth_controller = mocker.MagicMock()
    mocker.patch.dict(
        "sys.modules", {"auth_controller.controller": mocked_auth_controller}
    )

    # When
    serializer = CustomUserCreateSerializer(
        data=user_dict, context={"request": request}
    )

    serializer.is_valid(raise_exception=True)

    # Then
    mocked_auth_controller.is_authentication_method_valid.assert_called_with(
        request,
        email=user_dict["email"],
        raise_exception=True,
    )
