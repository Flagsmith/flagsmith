from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer, Serializer

from custom_auth.mfa.trench.exceptions import (
    CodeInvalidOrExpiredError,
    MFAMethodAlreadyActiveError,
)
from custom_auth.mfa.trench.models import MFAMethod
from custom_auth.mfa.trench.utils import get_mfa_handler, get_mfa_model

User: AbstractUser = get_user_model()  # type: ignore[assignment]


class MFAMethodActivationConfirmationValidator(Serializer):  # type: ignore[type-arg]
    code = CharField()

    def __init__(self, mfa_method_name: str, user: User, *args, **kwargs) -> None:  # type: ignore[no-untyped-def,valid-type]  # noqa: E501
        super().__init__(*args, **kwargs)
        self._user = user
        self._mfa_method_name = mfa_method_name

    def validate_code(self, value: str) -> str:
        mfa_model = get_mfa_model()
        mfa = mfa_model.objects.get_by_name(
            user_id=self._user.id, name=self._mfa_method_name  # type: ignore[attr-defined]
        )
        self._validate_mfa_method(mfa)

        handler = get_mfa_handler(mfa)

        if handler.validate_code(value):
            return value

        raise CodeInvalidOrExpiredError()

    @staticmethod
    def _validate_mfa_method(mfa: MFAMethod) -> None:
        if mfa.is_active:
            raise MFAMethodAlreadyActiveError()


class CodeLoginSerializer(Serializer):  # type: ignore[type-arg]
    ephemeral_token = CharField()
    code = CharField()


class UserMFAMethodSerializer(ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = get_mfa_model()
        fields = ("name", "is_primary")
