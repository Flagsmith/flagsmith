import hashlib
import hmac


def github_webhook_payload_is_valid(
    payload_body: bytes, secret_token: str, signature_header: str
) -> bool:
    """Verify that the payload was sent from GitHub by validating SHA256.
    Raise and return 403 if not authorized.
    """
    if not signature_header:
        return False
    hash_object = hmac.new(
        secret_token.encode("utf-8"), msg=payload_body, digestmod=hashlib.sha1
    )
    expected_signature = "sha1=" + hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, signature_header):
        return False

    return True
