import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from pytest_django.fixtures import SettingsWrapper

from integrations.github.client import generate_jwt_token


def test_generate_jwt_token__valid_credentials__returns_decodable_jwt(
    settings: SettingsWrapper,
) -> None:
    # Given
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    settings.GITHUB_PEM = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    app_id = 12345

    # When
    token = generate_jwt_token(app_id=app_id)

    # Then
    decoded = jwt.decode(
        token,
        private_key.public_key(),
        algorithms=["RS256"],
        options={"verify_exp": False},
    )
    assert decoded["iss"] == str(app_id)
