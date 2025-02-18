from typing import Iterable, Optional

from django.contrib.auth.hashers import check_password


def validate_backup_code_command(value: str, backup_codes: Iterable) -> Optional[str]:  # type: ignore[type-arg]
    for backup_code in backup_codes:
        if check_password(value, backup_code):
            return backup_code  # type: ignore[no-any-return]
    return None
