from typing import Callable, Set, Type

from django.contrib.auth.hashers import make_password

from custom_auth.mfa.trench.command.generate_backup_codes import (
    generate_backup_codes_command,
)
from custom_auth.mfa.trench.exceptions import MFAMethodDoesNotExistError
from custom_auth.mfa.trench.models import MFAMethod
from custom_auth.mfa.trench.settings import trench_settings
from custom_auth.mfa.trench.utils import get_mfa_model


class RegenerateBackupCodesForMFAMethodCommand:
    def __init__(
        self,
        requires_encryption: bool,
        mfa_model: Type[MFAMethod],
        code_hasher: Callable,
        codes_generator: Callable,
    ) -> None:
        self._requires_encryption = requires_encryption
        self._mfa_model = mfa_model
        self._code_hasher = code_hasher
        self._codes_generator = codes_generator

    def execute(self, user_id: int, name: str) -> Set[str]:
        backup_codes = self._codes_generator()
        rows_affected = self._mfa_model.objects.filter(
            user_id=user_id, name=name
        ).update(
            _backup_codes=MFAMethod._BACKUP_CODES_DELIMITER.join(
                [self._code_hasher(backup_code) for backup_code in backup_codes]
                if self._requires_encryption
                else backup_codes
            ),
        )

        if rows_affected < 1:
            raise MFAMethodDoesNotExistError()

        return backup_codes


regenerate_backup_codes_for_mfa_method_command = (
    RegenerateBackupCodesForMFAMethodCommand(
        requires_encryption=trench_settings.ENCRYPT_BACKUP_CODES,
        mfa_model=get_mfa_model(),
        code_hasher=make_password,
        codes_generator=generate_backup_codes_command,
    ).execute
)
