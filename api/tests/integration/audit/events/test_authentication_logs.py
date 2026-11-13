import pyotp
import pytest
import responses
from django.contrib.auth.hashers import make_password
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from audit.models import AuditLog
from custom_auth.mfa.trench.models import MFAMethod
from organisations.models import Organisation
from users.models import FFAdminUser


@pytest.fixture
def user(db: None) -> FFAdminUser:
    return FFAdminUser.objects.create(  # type: ignore[no-any-return]
        email="alice@example.com",
        password=make_password("password"),
    )


@pytest.fixture
def organisation(user: FFAdminUser) -> Organisation:
    organisation = Organisation.objects.create(name="Test org")
    user.add_organisation(organisation)
    return organisation  # type: ignore[no-any-return]


@pytest.fixture
def other_organisation(user: FFAdminUser) -> Organisation:
    organisation = Organisation.objects.create(name="Bananas Inc")
    user.add_organisation(organisation)
    return organisation  # type: ignore[no-any-return]


@pytest.fixture(autouse=True)
def unrelated_organisation(db: None) -> Organisation:
    return Organisation.objects.create(name="Grapes Ltd")  # type: ignore[no-any-return]


@pytest.fixture
def user_totp(user: FFAdminUser) -> pyotp.TOTP:
    """Enable 2FA outside the API, so it records no audit log."""
    secret = pyotp.random_base32()
    MFAMethod.objects.create(
        user=user,
        name="app",
        secret=secret,
        is_primary=True,
        is_active=True,
    )
    return pyotp.TOTP(secret)


@pytest.fixture
def user_client(api_client: APIClient, user: FFAdminUser) -> APIClient:
    """Authenticate outside the API, so it records no audit log."""
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client


def test_login__correct_credentials_2fa_disabled__creates_audit_log(
    api_client: APIClient,
    organisation: Organisation,
    other_organisation: Organisation,
    user: FFAdminUser,
) -> None:
    # Given / When
    response = api_client.post(
        "/api/v1/auth/login/",
        {"email": "alice@example.com", "password": "password"},
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert list(
        AuditLog.objects.order_by("organisation_id", "created_date").values(
            "organisation_id", "author_id", "log"
        )
    ) == [
        {
            "organisation_id": organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` logged in without 2FA.",
        },
        {
            "organisation_id": other_organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` logged in without 2FA.",
        },
    ]


def test_login__correct_credentials_2fa_enabled__creates_audit_log(
    api_client: APIClient,
    organisation: Organisation,
    other_organisation: Organisation,
    user: FFAdminUser,
    user_totp: pyotp.TOTP,
) -> None:
    # Given
    ephemeral_token = api_client.post(
        "/api/v1/auth/login/",
        {"email": "alice@example.com", "password": "password"},
        format="json",
    ).json()["ephemeral_token"]

    # When
    response = api_client.post(
        "/api/v1/auth/login/code/",
        {"ephemeral_token": ephemeral_token, "code": user_totp.now()},
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert list(
        AuditLog.objects.order_by("organisation_id", "created_date").values(
            "organisation_id", "author_id", "log"
        )
    ) == [
        {
            "organisation_id": organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` has entered their password but needs 2FA.",
        },
        {
            "organisation_id": organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` logged in with 2FA.",
        },
        {
            "organisation_id": other_organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` has entered their password but needs 2FA.",
        },
        {
            "organisation_id": other_organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` logged in with 2FA.",
        },
    ]


def test_login__incorrect_password__creates_audit_log(
    api_client: APIClient,
    organisation: Organisation,
    other_organisation: Organisation,
    user: FFAdminUser,
) -> None:
    # Given / When
    response = api_client.post(
        "/api/v1/auth/login/",
        {"email": "alice@example.com", "password": "incorrect"},
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert list(
        AuditLog.objects.order_by("organisation_id", "created_date").values(
            "organisation_id", "author_id", "log"
        )
    ) == [
        {
            "organisation_id": organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` failed to log in: incorrect password.",
        },
        {
            "organisation_id": other_organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` failed to log in: incorrect password.",
        },
    ]


def test_login__incorrect_2fa_code__creates_audit_log(
    api_client: APIClient,
    organisation: Organisation,
    other_organisation: Organisation,
    user: FFAdminUser,
    user_totp: pyotp.TOTP,
) -> None:
    # Given
    ephemeral_token = api_client.post(
        "/api/v1/auth/login/",
        {"email": "alice@example.com", "password": "password"},
        format="json",
    ).json()["ephemeral_token"]

    # When
    response = api_client.post(
        "/api/v1/auth/login/code/",
        {"ephemeral_token": ephemeral_token, "code": "incorrect"},
        format="json",
    )

    # Then
    assert response.status_code == 401
    assert list(
        AuditLog.objects.order_by("organisation_id", "created_date").values(
            "organisation_id", "author_id", "log"
        )
    ) == [
        {
            "organisation_id": organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` has entered their password but needs 2FA.",
        },
        {
            "organisation_id": organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` failed to log in: incorrect 2FA code.",
        },
        {
            "organisation_id": other_organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` has entered their password but needs 2FA.",
        },
        {
            "organisation_id": other_organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` failed to log in: incorrect 2FA code.",
        },
    ]


@responses.activate
def test_login__with_google_sso__creates_audit_log(
    api_client: APIClient,
    organisation: Organisation,
    other_organisation: Organisation,
    user: FFAdminUser,
) -> None:
    # Given
    responses.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        json={"id": "google-user-id", "email": "alice@example.com"},
    )

    # When
    response = api_client.post(
        "/api/v1/auth/oauth/google/",
        {"access_token": "google-access-token"},
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert list(
        AuditLog.objects.order_by("organisation_id", "created_date").values(
            "organisation_id", "author_id", "log"
        )
    ) == [
        {
            "organisation_id": organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` logged in with Google.",
        },
        {
            "organisation_id": other_organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` logged in with Google.",
        },
    ]


@responses.activate
def test_login__with_github_sso__creates_audit_log(
    api_client: APIClient,
    organisation: Organisation,
    other_organisation: Organisation,
    user: FFAdminUser,
) -> None:
    # Given
    responses.post(
        "https://github.com/login/oauth/access_token",
        body="access_token=github-access-token&token_type=bearer",
    )
    responses.get(
        "https://api.github.com/user",
        json={"id": 12345, "name": "Alice Example"},
    )
    responses.get(
        "https://api.github.com/user/emails",
        json=[{"email": "alice@example.com", "primary": True, "verified": True}],
    )

    # When
    response = api_client.post(
        "/api/v1/auth/oauth/github/",
        {"access_token": "github-code"},
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert list(
        AuditLog.objects.order_by("organisation_id", "created_date").values(
            "organisation_id", "author_id", "log"
        )
    ) == [
        {
            "organisation_id": organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` logged in with GitHub.",
        },
        {
            "organisation_id": other_organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` logged in with GitHub.",
        },
    ]


def test_logout__completed__creates_audit_log(
    organisation: Organisation,
    other_organisation: Organisation,
    user: FFAdminUser,
    user_client: APIClient,
) -> None:
    # Given / When
    response = user_client.post("/api/v1/auth/logout/")

    # Then
    assert response.status_code == 204
    assert list(
        AuditLog.objects.order_by("organisation_id", "created_date").values(
            "organisation_id", "author_id", "log"
        )
    ) == [
        {
            "organisation_id": organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` logged out.",
        },
        {
            "organisation_id": other_organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` logged out.",
        },
    ]


def test_change_password__completed__creates_audit_log(
    organisation: Organisation,
    other_organisation: Organisation,
    user: FFAdminUser,
    user_client: APIClient,
) -> None:
    # Given / When
    response = user_client.post(
        "/api/v1/auth/users/set_password/",
        {
            "current_password": "password",
            "new_password": "correct-horse-battery-staple",
            "re_new_password": "correct-horse-battery-staple",
        },
        format="json",
    )

    # Then
    assert response.status_code == 204
    assert list(
        AuditLog.objects.order_by("organisation_id", "created_date").values(
            "organisation_id", "author_id", "log"
        )
    ) == [
        {
            "organisation_id": organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` logged out.",
        },
        {
            "organisation_id": organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` changed their password.",
        },
        {
            "organisation_id": other_organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` logged out.",
        },
        {
            "organisation_id": other_organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` changed their password.",
        },
    ]


def test_enable_2fa__completed__creates_audit_log(
    organisation: Organisation,
    other_organisation: Organisation,
    user: FFAdminUser,
    user_client: APIClient,
) -> None:
    # Given
    secret = user_client.post("/api/v1/auth/app/activate/").json()["secret"]

    # When
    response = user_client.post(
        "/api/v1/auth/app/activate/confirm/",
        {"code": pyotp.TOTP(secret).now()},
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert list(
        AuditLog.objects.order_by("organisation_id", "created_date").values(
            "organisation_id", "author_id", "log"
        )
    ) == [
        {
            "organisation_id": organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` enabled 2FA.",
        },
        {
            "organisation_id": other_organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` enabled 2FA.",
        },
    ]


def test_disable_2fa__completed__creates_audit_log(
    organisation: Organisation,
    other_organisation: Organisation,
    user: FFAdminUser,
    user_client: APIClient,
    user_totp: pyotp.TOTP,
) -> None:
    # Given / When
    response = user_client.post("/api/v1/auth/app/deactivate/")

    # Then
    assert response.status_code == 204
    assert list(
        AuditLog.objects.order_by("organisation_id", "created_date").values(
            "organisation_id", "author_id", "log"
        )
    ) == [
        {
            "organisation_id": organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` disabled 2FA.",
        },
        {
            "organisation_id": other_organisation.id,
            "author_id": user.id,
            "log": "User `alice@example.com` disabled 2FA.",
        },
    ]
