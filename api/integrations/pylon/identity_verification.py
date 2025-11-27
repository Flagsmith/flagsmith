import hashlib
import hmac

from django.conf import settings


def get_user_email_signature(email: str) -> str:
    if not settings.PYLON_IDENTITY_VERIFICATION_SECRET:
        raise ValueError("PYLON_IDENTITY_VERIFICATION_SECRET is not set")
    secret_bytes = bytes.fromhex(settings.PYLON_IDENTITY_VERIFICATION_SECRET)
    signature = hmac.new(secret_bytes, email.encode(), hashlib.sha256).hexdigest()
    return signature
