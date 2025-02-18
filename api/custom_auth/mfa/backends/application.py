from typing import Any, Dict

from django.conf import settings
from pyotp import TOTP
from rest_framework.response import Response

from custom_auth.mfa.trench.models import MFAMethod


class CustomApplicationBackend:
    def __init__(self, mfa_method: MFAMethod, config: Dict[str, Any]) -> None:
        self._mfa_method = mfa_method
        self._config = config
        self._totp = TOTP(self._mfa_method.secret)

    def dispatch_message(self):  # type: ignore[no-untyped-def]
        qr_link = self._totp.provisioning_uri(
            self._mfa_method.user.email, settings.TRENCH_AUTH["APPLICATION_ISSUER_NAME"]  # type: ignore[arg-type]
        )
        data = {
            "qr_link": qr_link,
            "secret": self._mfa_method.secret,
        }
        return Response(data)

    def validate_code(self, code: str) -> bool:
        validity_period = settings.TRENCH_AUTH["MFA_METHODS"]["app"]["VALIDITY_PERIOD"]  # type: ignore[index]
        return self._totp.verify(otp=code, valid_window=int(validity_period / 20))
