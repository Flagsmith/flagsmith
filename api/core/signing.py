import hashlib
import hmac


def sign_payload(payload: str, key: str):  # type: ignore[no-untyped-def]
    # signPayload of frontend/web/components/TestWebHook on the frontend replicates this
    # exact function, change the function there if this changes.
    return hmac.new(
        key=key.encode(), msg=payload.encode(), digestmod=hashlib.sha256
    ).hexdigest()
