from typing import Any, Dict

from django.conf import settings
from pyotp import TOTP
from rest_framework.response import Response
from trench.models import MFAMethod


class CustomApplicationBackend:
    def __init__(self, mfa_method: MFAMethod, config: Dict[str, Any]) -> None:
        self._mfa_method = mfa_method
        self._config = config
        self._totp = TOTP(self._mfa_method.secret)

    def dispatch_message(self):
        qr_link = self._totp.provisioning_uri(
            self._mfa_method.user.email, settings.TRENCH_AUTH["APPLICATION_ISSUER_NAME"]
        )
        data = {
            "qr_link": qr_link,
            "secret": self._mfa_method.secret,
        }
        return Response(data)

    def confirm_activation(self, code: str) -> None:
        pass

    def validate_confirmation_code(self, code: str) -> bool:
        return self.validate_code(code)

    def validate_code(self, code: str) -> bool:
        return self._totp.verify(otp=code, valid_window=20)
