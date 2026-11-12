from typing import Type

from django.db.transaction import atomic

from custom_auth.mfa.trench.exceptions import MFANotEnabledError
from custom_auth.mfa.trench.models import MFAMethod
from custom_auth.mfa.trench.utils import get_mfa_model


class DeactivateMFAMethodCommand:
    def __init__(self, mfa_model: Type[MFAMethod]) -> None:
        self._mfa_model = mfa_model

    @atomic
    def execute(self, mfa_method_name: str, user_id: int) -> None:
        mfa = self._mfa_model.objects.get_by_name(user_id=user_id, name=mfa_method_name)
        if not mfa.is_active:
            raise MFANotEnabledError()

        self._mfa_model.objects.filter(user_id=user_id, name=mfa_method_name).update(
            is_active=False, is_primary=False
        )


deactivate_mfa_method_command = DeactivateMFAMethodCommand(
    mfa_model=get_mfa_model()
).execute
