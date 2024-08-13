from typing import Any, Iterable

from django.conf import settings
from django.db.models import (
    CASCADE,
    BooleanField,
    CharField,
    ForeignKey,
    Manager,
    Model,
    QuerySet,
    TextField,
)

from custom_auth.mfa.trench.exceptions import MFAMethodDoesNotExistError


class MFAUserMethodManager(Manager):
    def get_by_name(self, user_id: Any, name: str) -> "MFAMethod":
        try:
            return self.get(user_id=user_id, name=name)
        except self.model.DoesNotExist:
            raise MFAMethodDoesNotExistError()

    def get_primary_active(self, user_id: Any) -> "MFAMethod":
        try:
            return self.get(user_id=user_id, is_primary=True, is_active=True)
        except self.model.DoesNotExist:
            raise MFAMethodDoesNotExistError()

    def list_active(self, user_id: Any) -> QuerySet:
        return self.filter(user_id=user_id, is_active=True)

    def primary_exists(self, user_id: Any) -> bool:
        return self.filter(user_id=user_id, is_primary=True).exists()


class MFAMethod(Model):
    _BACKUP_CODES_DELIMITER = ","

    user = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        verbose_name="user",
        related_name="mfa_methods",
    )
    name = CharField("name", max_length=255)
    secret = CharField("secret", max_length=255)
    is_primary = BooleanField("is primary", default=False)
    is_active = BooleanField("is active", default=False)
    _backup_codes = TextField("backup codes", blank=True)

    class Meta:
        verbose_name = "MFA Method"
        verbose_name_plural = "MFA Methods"

    objects = MFAUserMethodManager()

    @property
    def backup_codes(self) -> Iterable[str]:
        return self._backup_codes.split(self._BACKUP_CODES_DELIMITER)
