from typing import Any, Dict

from custom_auth.mfa.trench.exceptions import MFAMethodDoesNotExistError
from custom_auth.mfa.trench.settings import TrenchAPISettings, trench_settings


class GetMFAConfigByNameQuery:
    def __init__(self, settings: TrenchAPISettings) -> None:
        self._settings = settings

    def execute(self, name: str) -> Dict[str, Any]:
        try:
            return self._settings.MFA_METHODS[name]
        except KeyError as cause:
            raise MFAMethodDoesNotExistError from cause


get_mfa_config_by_name_query = GetMFAConfigByNameQuery(settings=trench_settings).execute
