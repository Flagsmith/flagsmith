from typing import Iterable, Optional

from django.contrib.auth.hashers import check_password

from custom_auth.mfa.trench.settings import trench_settings


def validate_backup_code_command(value: str, backup_codes: Iterable) -> Optional[str]:
    settings = trench_settings
    if not settings.ENCRYPT_BACKUP_CODES:
        return value if value in backup_codes else None
    for backup_code in backup_codes:
        if check_password(value, backup_code):
            return backup_code
    return None
