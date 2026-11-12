from typing import Callable, Set, Type

from django.contrib.auth.hashers import make_password

from custom_auth.mfa.trench.command.generate_backup_codes import (
    generate_backup_codes_command,
)
from custom_auth.mfa.trench.models import MFAMethod
from custom_auth.mfa.trench.utils import get_mfa_model


class RegenerateBackupCodesForMFAMethodCommand:
    def __init__(
        self,
        mfa_model: Type[MFAMethod],
        code_hasher: Callable,  # type: ignore[type-arg]
        codes_generator: Callable,  # type: ignore[type-arg]
    ) -> None:
        self._mfa_model = mfa_model
        self._code_hasher = code_hasher
        self._codes_generator = codes_generator

    def execute(self, user_id: int, name: str) -> Set[str]:
        backup_codes = self._codes_generator()
        self._mfa_model.objects.filter(user_id=user_id, name=name).update(
            _backup_codes=MFAMethod._BACKUP_CODES_DELIMITER.join(
                [self._code_hasher(backup_code) for backup_code in backup_codes]
            ),
        )
        return backup_codes  # type: ignore[no-any-return]


regenerate_backup_codes_for_mfa_method_command = (
    RegenerateBackupCodesForMFAMethodCommand(
        mfa_model=get_mfa_model(),
        code_hasher=make_password,
        codes_generator=generate_backup_codes_command,
    ).execute
)
