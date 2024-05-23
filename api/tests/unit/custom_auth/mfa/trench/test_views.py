import pyotp
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from custom_auth.mfa.trench.models import MFAMethod


def test_list_user_active_methods(admin_client: APIClient, mfa_app_method: MFAMethod):
    # Given
    url = reverse("api-v1:custom_auth:mfa-list-user-active-methods")

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {"name": mfa_app_method.name, "is_primary": mfa_app_method.is_primary}
    ]


def test_deactivate_user_active_method(
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


def test_activate_wrong_method_returns_404(admin_client: APIClient):
    # Given
    url = reverse("api-v1:custom_auth:mfa-activate", kwargs={"method": "wrong_method"})

    # When
    response = admin_client.post(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_activate_confirm_with_wrong_method_returns_400(
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


def test_activate_confirm_without_code_returns_400(
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
