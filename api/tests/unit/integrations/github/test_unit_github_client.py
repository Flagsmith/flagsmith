import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from integrations.github.client import generate_jwt_token, generate_token


@pytest.fixture()
def rsa_private_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(autouse=True)
def github_pem(settings: SettingsWrapper, rsa_private_key: rsa.RSAPrivateKey) -> None:
    settings.GITHUB_PEM = rsa_private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()


def test_generate_token__valid_credentials__returns_installation_token(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_installation_auth = mocker.MagicMock()
    mock_installation_auth.token = "installation-token"
    mocker.patch(
        "integrations.github.client.Auth.AppAuth.get_installation_auth",
        return_value=mock_installation_auth,
    )
    mocker.patch("integrations.github.client.Github")

    # When
    result = generate_token(installation_id="12345", app_id=67890)

    # Then
    assert result == "installation-token"


def test_generate_jwt_token__valid_credentials__returns_decodable_jwt(
    rsa_private_key: rsa.RSAPrivateKey,
) -> None:
    # Given
    app_id = 12345

    # When
    token = generate_jwt_token(app_id=app_id)

    # Then
    decoded = jwt.decode(
        token,
        rsa_private_key.public_key(),
        algorithms=["RS256"],
        options={"verify_exp": False},
    )
    assert decoded["iss"] == str(app_id)
