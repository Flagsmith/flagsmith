import string
from typing import Any, Dict

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework.settings import APISettings, perform_import

from custom_auth.mfa.trench.exceptions import MethodHandlerMissingError


class TrenchAPISettings(APISettings):
    _FIELD_USER_SETTINGS = "_user_settings"
    _FIELD_TRENCH_AUTH = "TRENCH_AUTH"
    _FIELD_BACKUP_CODES_CHARACTERS = "BACKUP_CODES_CHARACTERS"
    _FIELD_MFA_METHODS = "MFA_METHODS"
    _FIELD_HANDLER = "HANDLER"

    @property
    def user_settings(self) -> Dict[str, Any]:
        if not hasattr(self, self._FIELD_USER_SETTINGS):
            self._user_settings = getattr(settings, self._FIELD_TRENCH_AUTH, {})
        return self._user_settings

    def __getattr__(self, attr: str) -> Any:
        val = super().__getattr__(attr)
        self._validate(attribute=attr, value=val)
        return val

    def _validate(self, attribute: str, value: Any) -> None:
        if attribute == self._FIELD_MFA_METHODS:
            for method_name, method_config in value.items():
                if self._FIELD_HANDLER not in method_config:
                    raise MethodHandlerMissingError(method_name=method_name)
                for k, v in self.defaults[self._FIELD_MFA_METHODS][method_name].items():
                    method_config[k] = method_config.get(k, v)
                method_config[self._FIELD_HANDLER] = perform_import(
                    method_config[self._FIELD_HANDLER], self._FIELD_HANDLER
                )

    def __getitem__(self, attr: str) -> Any:
        return self.__getattr__(attr)


HANDLER = "HANDLER"
VALIDITY_PERIOD = "VALIDITY_PERIOD"
VERBOSE_NAME = "VERBOSE_NAME"

DEFAULTS = {
    "USER_ACTIVE_FIELD": "is_active",
    "BACKUP_CODES_QUANTITY": 5,
    "BACKUP_CODES_LENGTH": 12,  # keep (quantity * length) under 200
    "BACKUP_CODES_CHARACTERS": (string.ascii_letters + string.digits),
    "SECRET_KEY_LENGTH": 32,
    "DEFAULT_VALIDITY_PERIOD": 30,
    "CONFIRM_DISABLE_WITH_CODE": False,
    "CONFIRM_BACKUP_CODES_REGENERATION_WITH_CODE": True,
    "ALLOW_BACKUP_CODES_REGENERATION": True,
    "ENCRYPT_BACKUP_CODES": True,
    "APPLICATION_ISSUER_NAME": "MyApplication",
    "MFA_METHODS": {
        "app": {
            VERBOSE_NAME: _("app"),
            VALIDITY_PERIOD: 30,
            "USES_THIRD_PARTY_CLIENT": True,
            HANDLER: "trench.backends.application.ApplicationMessageDispatcher",
        }
    },
}

trench_settings = TrenchAPISettings(
    user_settings=None, defaults=DEFAULTS, import_strings=None
)
