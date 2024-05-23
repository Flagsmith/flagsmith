from abc import abstractmethod

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer, Serializer

from custom_auth.mfa.trench.command.remove_backup_code import (
    remove_backup_code_command,
)
from custom_auth.mfa.trench.command.validate_backup_code import (
    validate_backup_code_command,
)
from custom_auth.mfa.trench.exceptions import (
    CodeInvalidOrExpiredError,
    MFAMethodAlreadyActiveError,
    MFANotEnabledError,
    OTPCodeMissingError,
)
from custom_auth.mfa.trench.models import MFAMethod
from custom_auth.mfa.trench.settings import trench_settings
from custom_auth.mfa.trench.utils import get_mfa_handler, get_mfa_model

User: AbstractUser = get_user_model()


class ProtectedActionValidator(Serializer):
    code = CharField()

    @staticmethod
    def _get_validation_method_name() -> str:
        return "validate_code"

    @staticmethod
    @abstractmethod
    def _validate_mfa_method(mfa: MFAMethod) -> None:
        raise NotImplementedError

    def __init__(self, mfa_method_name: str, user: User, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._user = user
        self._mfa_method_name = mfa_method_name

    def validate_code(self, value: str) -> str:
        if not value:
            raise OTPCodeMissingError()
        mfa_model = get_mfa_model()
        mfa = mfa_model.objects.get_by_name(
            user_id=self._user.id, name=self._mfa_method_name
        )
        self._validate_mfa_method(mfa)

        validated_backup_code = validate_backup_code_command(
            value=value, backup_codes=mfa.backup_codes
        )

        handler = get_mfa_handler(mfa)
        validation_method = getattr(handler, self._get_validation_method_name())
        if validation_method(value):
            return value

        if validated_backup_code:
            remove_backup_code_command(
                user_id=mfa.user_id, method_name=mfa.name, code=value
            )
            return value

        raise CodeInvalidOrExpiredError()


class MFAMethodDeactivationValidator(ProtectedActionValidator):
    code = CharField(required=trench_settings.CONFIRM_DISABLE_WITH_CODE)

    @staticmethod
    def _validate_mfa_method(mfa: MFAMethod) -> None:
        if not mfa.is_active:
            raise MFANotEnabledError()


class MFAMethodActivationConfirmationValidator(ProtectedActionValidator):
    @staticmethod
    def _get_validation_method_name() -> str:
        return "validate_confirmation_code"

    @staticmethod
    def _validate_mfa_method(mfa: MFAMethod) -> None:
        if mfa.is_active:
            raise MFAMethodAlreadyActiveError()


class CodeLoginSerializer(Serializer):
    ephemeral_token = CharField()
    code = CharField()


class UserMFAMethodSerializer(ModelSerializer):
    class Meta:
        model = get_mfa_model()
        fields = ("name", "is_primary")
