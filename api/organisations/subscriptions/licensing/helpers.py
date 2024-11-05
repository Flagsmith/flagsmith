import base64
import logging

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from django.conf import settings

logger: logging.Logger = logging.getLogger(name=__name__)


class PrivateKeyMissingError(RuntimeError):
    pass


def sign_licence(licence: str) -> str:
    message = licence.encode("utf-8")

    if not settings.SUBSCRIPTION_LICENCE_PRIVATE_KEY:
        raise PrivateKeyMissingError("Private key is missing")

    # Load the private key from PEM
    private_key = serialization.load_pem_private_key(
        settings.SUBSCRIPTION_LICENCE_PRIVATE_KEY.encode("utf-8"), password=None
    )

    # Sign the message using the private key
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )

    return base64.b64encode(signature).decode("utf-8")


def verify_signature(licence: str, licence_signature: str) -> bool:
    signature = base64.b64decode(licence_signature)
    public_key = serialization.load_pem_public_key(
        settings.SUBSCRIPTION_LICENCE_PUBLIC_KEY.encode("utf-8")
    )

    try:
        public_key.verify(
            signature,
            licence.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )
    except Exception:
        logger.error("Licence signature failed", exc_info=True)
        return False

    return True


def create_public_key() -> str:
    """
    Creates a public key from the private key that's set in settings.
    """

    # Load the private key from the UTF-8 PEM string.
    private_key = serialization.load_pem_private_key(
        settings.SUBSCRIPTION_LICENCE_PRIVATE_KEY.encode("utf-8"),
        password=None,
        backend=default_backend(),
    )

    # Extract the public key from the private key.
    public_key = private_key.public_key()

    # Encode the public key to PEM format
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    return public_key_pem.decode("utf-8")


def create_private_key() -> str:
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    # Convert the private key to PEM format as a byte string
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Print the PEM-encoded private key to standard output
    return private_key_pem.decode("utf-8")
