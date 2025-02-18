import pyotp
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from custom_auth.mfa.trench.models import MFAMethod
from users.models import FFAdminUser


def test_list_user_active_methods(admin_client: APIClient, mfa_app_method: MFAMethod):  # type: ignore[no-untyped-def]
    # Given
    url = reverse("api-v1:custom_auth:mfa-list-user-active-methods")

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {"name": mfa_app_method.name, "is_primary": mfa_app_method.is_primary}
    ]


def test_deactivate_user_active_method(  # type: ignore[no-untyped-def]
    admin_client: APIClient, mfa_app_method: MFAMethod
):
    # Given
    url = reverse("api-v1:custom_auth:mfa-deactivate", args=[mfa_app_method.name])

    # When
    response = admin_client.post(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    mfa_app_method.refresh_from_db()
    assert mfa_app_method.is_active is False


def test_deactivate_already_deactivated_mfa_returns_400(  # type: ignore[no-untyped-def]
    admin_client: APIClient, mfa_app_method: MFAMethod
):
    # Given
    mfa_app_method.is_active = False
    mfa_app_method.is_primary = False
    mfa_app_method.save()

    url = reverse("api-v1:custom_auth:mfa-deactivate", args=[mfa_app_method.name])

    # When
    response = admin_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "2FA is not enabled."


def test_activate_wrong_method_returns_404(admin_client: APIClient):  # type: ignore[no-untyped-def]
    # Given
    url = reverse("api-v1:custom_auth:mfa-activate", kwargs={"method": "wrong_method"})

    # When
    response = admin_client.post(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_activate_mfa_with_existing_mfa_returns_400(  # type: ignore[no-untyped-def]
    admin_client: APIClient, mfa_app_method: MFAMethod
):
    # Given
    url = reverse("api-v1:custom_auth:mfa-activate", kwargs={"method": "app"})

    # When
    response = admin_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "MFA method already active."


def test_activate_confirm_with_wrong_method_returns_400(  # type: ignore[no-untyped-def]
    admin_client: APIClient, mfa_app_method: MFAMethod
):
    # Given
    totp = pyotp.TOTP(mfa_app_method.secret)
    url = reverse(
        "api-v1:custom_auth:mfa-activate-confirm", kwargs={"method": "wrong_method"}
    )

    # When
    data = {"code": totp.now()}
    response = admin_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"code": ["Requested MFA method does not exist."]}


def test_activate_confirm_already_active_mfa_returns_400(  # type: ignore[no-untyped-def]
    admin_client: APIClient, mfa_app_method: MFAMethod
):
    # Given
    totp = pyotp.TOTP(mfa_app_method.secret)
    url = reverse("api-v1:custom_auth:mfa-activate-confirm", kwargs={"method": "app"})

    # When
    data = {"code": totp.now()}
    response = admin_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"code": ["MFA method already active."]}


def test_re_activate_confirm_deactive_mfa_creates_new_backup_codes(  # type: ignore[no-untyped-def]
    admin_client: APIClient, deactivated_mfa_app_method: MFAMethod
):
    # Given
    existing_backup_codes = deactivated_mfa_app_method
    totp = pyotp.TOTP(deactivated_mfa_app_method.secret)
    url = reverse("api-v1:custom_auth:mfa-activate-confirm", kwargs={"method": "app"})

    # When
    data = {"code": totp.now()}
    response = admin_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_200_OK
    new_backup_codes = response.json()["backup_codes"]
    for code in existing_backup_codes.backup_codes:
        assert code not in new_backup_codes


def test_activate_confirm_mfa_for_different_user_retuns_400(  # type: ignore[no-untyped-def]
    staff_client: APIClient, deactivated_mfa_app_method: MFAMethod
):
    # Given
    totp = pyotp.TOTP(deactivated_mfa_app_method.secret)
    url = reverse("api-v1:custom_auth:mfa-activate-confirm", kwargs={"method": "app"})

    # When
    data = {"code": totp.now()}
    response = staff_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_activate_confirm_without_code_returns_400(  # type: ignore[no-untyped-def]
    admin_client: APIClient, mfa_app_method: MFAMethod
):
    # Given
    url = reverse(
        "api-v1:custom_auth:mfa-activate-confirm",
        kwargs={"method": mfa_app_method.name},
    )

    # When
    response = admin_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"code": ["This field is required."]}


def test_activate_confirm_with_wrong_code_returns_400(  # type: ignore[no-untyped-def]
    admin_client: APIClient, mfa_app_method: MFAMethod
):
    # Given
    mfa_app_method.is_active = False
    mfa_app_method.is_primary = False
    mfa_app_method.save()

    url = reverse(
        "api-v1:custom_auth:mfa-activate-confirm",
        kwargs={"method": mfa_app_method.name},
    )
    data = {"code": "wrong_code"}
    # When
    response = admin_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"code": ["Code invalid or expired."]}


def test_login_with_invalid_mfa_code_returns_401(  # type: ignore[no-untyped-def]
    api_client: APIClient, admin_user: FFAdminUser, mfa_app_method: MFAMethod
):
    # Given
    login_url = reverse("api-v1:custom_auth:custom-mfa-authtoken-login")
    data = {"email": admin_user.email, "password": "password"}

    login_response = api_client.post(login_url, data=data)

    ephemeral_token = login_response.json()["ephemeral_token"]
    confirm_login_data = {"ephemeral_token": ephemeral_token, "code": "wrong_code"}
    login_confirm_url = reverse("api-v1:custom_auth:mfa-authtoken-login-code")

    # When
    login_confirm_response = api_client.post(login_confirm_url, data=confirm_login_data)

    # Then
    assert login_confirm_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert login_confirm_response.json() == {"error": "Invalid or expired code."}


def test_login_with_invalid_mfa_token_returns_401(  # type: ignore[no-untyped-def]
    api_client: APIClient, mfa_app_method: MFAMethod
):
    # Given
    totp = pyotp.TOTP(mfa_app_method.secret)
    data = {"ephemeral_token": "wrong_token", "code": totp.now()}
    url = reverse("api-v1:custom_auth:mfa-authtoken-login-code")

    # When
    login_confirm_response = api_client.post(url, data=data)

    # Then
    assert login_confirm_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert login_confirm_response.json() == {"error": "Invalid or expired token."}
