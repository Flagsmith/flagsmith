from typing import Any, Optional, Set

from django.contrib.auth.hashers import check_password

from custom_auth.mfa.trench.models import MFAMethod


def remove_backup_code_command(user_id: Any, method_name: str, code: str) -> None:
    serialized_codes = (
        MFAMethod.objects.filter(user_id=user_id, name=method_name)
        .values_list("_backup_codes", flat=True)
        .first()
    )
    codes = MFAMethod._BACKUP_CODES_DELIMITER.join(
        _remove_code_from_set(  # type: ignore[arg-type]
            backup_codes=set(serialized_codes.split(MFAMethod._BACKUP_CODES_DELIMITER)),
            code=code,
        )
    )
    MFAMethod.objects.filter(user_id=user_id, name=method_name).update(
        _backup_codes=codes
    )


def _remove_code_from_set(backup_codes: Set[str], code: str) -> Optional[Set[str]]:  # type: ignore[return]
    for backup_code in backup_codes:
        if check_password(code, backup_code):
            backup_codes.remove(backup_code)
            return backup_codes
