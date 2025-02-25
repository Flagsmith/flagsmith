from typing import Callable, Set, Type

from custom_auth.mfa.trench.command.generate_backup_codes import (
    generate_backup_codes_command,
)
from custom_auth.mfa.trench.command.replace_mfa_method_backup_codes import (
    regenerate_backup_codes_for_mfa_method_command,
)
from custom_auth.mfa.trench.models import MFAMethod
from custom_auth.mfa.trench.utils import get_mfa_model


class ActivateMFAMethodCommand:
    def __init__(
        self,
        mfa_model: Type[MFAMethod],
        backup_codes_generator: Callable,  # type: ignore[type-arg]
    ) -> None:
        self._mfa_model = mfa_model
        self._backup_codes_generator = backup_codes_generator

    def execute(self, user_id: int, name: str, code: str) -> Set[str]:
        self._mfa_model.objects.filter(user_id=user_id, name=name).update(
            is_active=True,
            is_primary=not self._mfa_model.objects.primary_exists(user_id=user_id),
        )

        backup_codes = regenerate_backup_codes_for_mfa_method_command(
            user_id=user_id,
            name=name,
        )

        return backup_codes


activate_mfa_method_command = ActivateMFAMethodCommand(
    mfa_model=get_mfa_model(),
    backup_codes_generator=generate_backup_codes_command,
).execute
