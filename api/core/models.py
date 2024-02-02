import logging
import typing
import uuid

from django.db import models
from django.db.models import Manager
from django.forms import model_to_dict
from django.http import HttpRequest
from simple_history.models import HistoricalRecords, ModelChange
from softdelete.models import SoftDeleteManager, SoftDeleteObject

from audit.related_object_type import RelatedObjectType

if typing.TYPE_CHECKING:
    from environments.models import Environment
    from projects.models import Project
    from users.models import FFAdminUser


logger = logging.getLogger(__name__)


class UUIDNaturalKeyManagerMixin:
    def get_by_natural_key(self, uuid_: str):
        logger.debug("Getting model %s by natural key", self.model.__name__)
        return self.get(uuid=uuid_)


class AbstractBaseExportableModelManager(UUIDNaturalKeyManagerMixin, Manager):
    pass


class AbstractBaseExportableModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    objects = AbstractBaseExportableModelManager()

    class Meta:
        abstract = True

    def natural_key(self):
        return (str(self.uuid),)


class SoftDeleteExportableManager(UUIDNaturalKeyManagerMixin, SoftDeleteManager):
    pass


class SoftDeleteExportableModel(SoftDeleteObject, AbstractBaseExportableModel):
    objects = SoftDeleteExportableManager()

    class Meta:
        abstract = True


class _BaseHistoricalModel(models.Model):
    include_in_audit = True
    _show_change_details_for_create = False

    master_api_key = models.ForeignKey(
        "api_keys.MasterAPIKey", blank=True, null=True, on_delete=models.DO_NOTHING
    )

    class Meta:
        abstract = True

    def get_change_details(self) -> typing.Optional[typing.List[ModelChange]]:
        if self.history_type == "~":
            return [
                change
                for change in self.diff_against(self.prev_record).changes
                if change.field not in self._change_details_excluded_fields
            ]
        elif self.history_type == "+" and self._show_change_details_for_create:
            return [
                ModelChange(field_name=key, old_value=None, new_value=value)
                for key, value in self.instance.to_dict().items()
                if key not in self._change_details_excluded_fields
            ]
        elif self.history_type == "-":
            # Ignore deletes because they get painful due to cascade deletes
            # Maybe we can resolve this in the future but for now it's not
            # critical.
            return []


def base_historical_model_factory(
    change_details_excluded_fields: typing.Sequence[str],
    show_change_details_for_create: bool = False,
) -> typing.Type[_BaseHistoricalModel]:
    class BaseHistoricalModel(_BaseHistoricalModel):
        _change_details_excluded_fields = set(change_details_excluded_fields)
        _show_change_details_for_create = show_change_details_for_create

        class Meta:
            abstract = True

    return BaseHistoricalModel


class _AbstractBaseAuditableModel(models.Model):
    """
    A base Model class that all models we want to be included in the audit log should inherit from.

    Some field descriptions:

     :history_record_class_path: the python class path to the HistoricalRecord model class.
        e.g. features.models.HistoricalFeature
     :related_object_type: a RelatedObjectType enum representing the related object type of the model.
        Note that this can be overridden by the `get_related_object_type` method in cases where it's
        different for certain scenarios.
    """

    history_record_class_path = None
    related_object_type = None

    to_dict_excluded_fields: typing.Sequence[str] = None
    to_dict_included_fields: typing.Sequence[str] = None

    class Meta:
        abstract = True

    def get_skip_create_audit_log(self) -> bool:
        return False

    def get_create_log_message(self, history_instance) -> typing.Optional[str]:
        """Override if audit log records should be written when model is created"""
        return None

    def get_update_log_message(self, history_instance) -> typing.Optional[str]:
        """Override if audit log records should be written when model is updated"""
        return None

    def get_delete_log_message(self, history_instance) -> typing.Optional[str]:
        """Override if audit log records should be written when model is deleted"""
        return None

    def get_environment_and_project(
        self,
    ) -> typing.Tuple[typing.Optional["Environment"], typing.Optional["Project"]]:
        environment, project = self._get_environment(), self._get_project()
        if not (environment or project):
            raise RuntimeError(
                "One of _get_environment() or _get_project() must "
                "be implemented and return a non-null value"
            )
        return environment, project

    def get_extra_audit_log_kwargs(self, history_instance) -> dict:
        """Add extra kwargs to the creation of the AuditLog record"""
        return {}

    def get_audit_log_author(self, history_instance) -> typing.Optional["FFAdminUser"]:
        """Override the AuditLog author (in cases where history_user isn't populated for example)"""
        return None

    def get_audit_log_related_object_id(self, history_instance) -> int:
        """Override the related object ID in cases where it shouldn't be self.id"""
        return self.id

    def get_audit_log_related_object_type(self, history_instance) -> RelatedObjectType:
        """
        Override the related object type to account for writing audit logs for related objects
        when certain events happen on this model.
        """
        return self.related_object_type

    def to_dict(self) -> dict[str, typing.Any]:
        # by default, we exclude the id and any foreign key fields from the response
        return model_to_dict(
            instance=self,
            fields=[
                f.name
                for f in self._meta.fields
                if f.name != "id" and not f.related_model
            ],
        )

    def _get_environment(self) -> typing.Optional["Environment"]:
        """Return the related environment for this model."""
        return None

    def _get_project(self) -> typing.Optional["Project"]:
        """Return the related project for this model."""
        return None


def get_history_user(
    instance: typing.Any, request: HttpRequest
) -> typing.Optional["FFAdminUser"]:
    user = getattr(request, "user", None)
    return None if getattr(user, "is_master_api_key_user", False) else user


def abstract_base_auditable_model_factory(
    historical_records_excluded_fields: typing.List[str] = None,
    change_details_excluded_fields: typing.Sequence[str] = None,
    show_change_details_for_create: bool = False,
) -> typing.Type[_AbstractBaseAuditableModel]:
    class Base(_AbstractBaseAuditableModel):
        history = HistoricalRecords(
            bases=[
                base_historical_model_factory(
                    change_details_excluded_fields or [],
                    show_change_details_for_create,
                )
            ],
            excluded_fields=historical_records_excluded_fields or [],
            get_user=get_history_user,
            inherit=True,
        )

        class Meta:
            abstract = True

    return Base
