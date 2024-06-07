from custom_auth.mfa.trench.command.remove_backup_code import (
    remove_backup_code_command,
)
from custom_auth.mfa.trench.command.validate_backup_code import (
    validate_backup_code_command,
)
from custom_auth.mfa.trench.exceptions import (
    InvalidCodeError,
    InvalidTokenError,
)
from custom_auth.mfa.trench.models import MFAMethod
from custom_auth.mfa.trench.utils import get_mfa_handler, user_token_generator
from users.models import FFAdminUser


def is_authenticated(user_id: int, code: str) -> None:
    for auth_method in MFAMethod.objects.list_active(user_id=user_id):
        validated_backup_code = validate_backup_code_command(
            value=code, backup_codes=auth_method.backup_codes
        )
        if get_mfa_handler(mfa_method=auth_method).validate_code(code=code):
            return
        if validated_backup_code:
            remove_backup_code_command(
                user_id=auth_method.user_id, method_name=auth_method.name, code=code
            )
            return
    raise InvalidCodeError()


def authenticate_second_step_command(code: str, ephemeral_token: str) -> FFAdminUser:
    user = user_token_generator.check_token(user=None, token=ephemeral_token)
    if user is None:
        raise InvalidTokenError()
    is_authenticated(user_id=user.id, code=code)
    return user
