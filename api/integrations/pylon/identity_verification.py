import hashlib
import hmac

from django.conf import settings


def get_user_email_signature(email: str) -> str | None:
    if not settings.PYLON_IDENTITY_VERIFICATION_SECRET:
        return None

    secret_bytes = bytes.fromhex(settings.PYLON_IDENTITY_VERIFICATION_SECRET)
    signature = hmac.new(secret_bytes, email.encode(), hashlib.sha256).hexdigest()
    return signature
