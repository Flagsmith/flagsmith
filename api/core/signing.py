import hashlib
import hmac


def sign_payload(payload: str, key: str):
    return hmac.new(
        key=key.encode(), msg=payload.encode(), digestmod=hashlib.sha256
    ).hexdigest()
