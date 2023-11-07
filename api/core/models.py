from __future__ import annotations

import functools
import logging
import typing
import uuid

from django.conf import settings
from django.db import models
from django.db.models import Manager
from django.http import HttpRequest
from django.utils import timezone
from simple_history import register
from simple_history.models import HistoricalRecords as BaseHistoricalRecords
from simple_history.models import (
    ModelChange,
    ModelDelta,
    post_create_historical_m2m_records,
    post_create_historical_record,
    pre_create_historical_m2m_records,
    pre_create_historical_record,
)
from softdelete.models import SoftDeleteManager, SoftDeleteObject

from audit.constants import CREATED_MESSAGE, DELETED_MESSAGE, UPDATED_MESSAGE
from audit.related_object_type import RelatedObjectType

if typing.TYPE_CHECKING:
    from environments.models import Environment
    from organisations.models import Organisation
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


class BaseHistoricalModel(models.Model):
    include_in_audit = True

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    master_api_key = models.ForeignKey(
        "api_keys.MasterAPIKey", blank=True, null=True, on_delete=models.DO_NOTHING
    )

    class Meta:
        abstract = True


class _AbstractBaseAuditableModel(models.Model):
    """
    A base Model class that all models we want to be included in the audit log should inherit from.

    Some field descriptions:

     :related_object_type: a RelatedObjectType enum representing the related object type of the model.
        Note that this can be overridden by the `get_related_object_type` method in cases where it's
        different for certain scenarios.
    """

    related_object_type: RelatedObjectType

    class Meta:
        abstract = True

    def get_create_log_message(self, history_instance) -> str | None:
        """Override if audit log records should be written when model is created"""
        return None

    def get_update_log_message(self, history_instance, delta: ModelDelta) -> str | None:
        """Override if audit log records should be written when model is updated"""
        return None

    def get_delete_log_message(self, history_instance) -> str | None:
        """Override if audit log records should be written when model is deleted"""
        return None

    def get_organisations_project_environment(
        self, delta: ModelDelta | None
    ) -> tuple[typing.Iterable[Organisation], Project | None, Environment | None]:
        # attempt to get environment to log against
        environment = self._get_environment(delta)
        # attempt to get project to log against, falling back to environment (if any) project
        project = self._get_project(delta) or (
            environment.project if environment else None
        )
        # attempt to get organisations to log against, falling back to project (if any) organisations
        # (organisations may be [] e.g. for an organisation-less user, but must not be None)
        if (organisations := self._get_organisations(delta)) is None:
            organisations = [project.organisation] if project else None
        # it should never be the case that we still don't know the organisations
        if organisations is None:
            raise RuntimeError(
                f"{self.__class__.__name__}: One of _get_organisations(), _get_project() or _get_environment() must "
                "be implemented and return a non-null value"
            )
        return organisations, project, environment

    def get_extra_audit_log_kwargs(self, history_instance) -> dict:
        """Add extra kwargs to the creation of the AuditLog record"""
        return {}

    def get_audit_log_author(self, history_instance) -> FFAdminUser | None:
        """Override the AuditLog author (in cases where history_user isn't populated for example)"""
        return None

    def get_audit_log_related_object_id(self, history_instance) -> int | None:
        """Override the related object ID in cases where it shouldn't be self.id"""
        return self.pk

    def get_audit_log_related_object_type(
        self, history_instance
    ) -> RelatedObjectType | None:
        """
        Override the related object type to account for writing audit logs for related objects
        when certain events happen on this model.
        """
        return self.related_object_type

    def get_audit_log_identity(self) -> str:
        """Override the human-readable identity for the related object"""
        return str(self)

    def get_audit_log_model_name(self, history_instance) -> str:
        """Override the human-readable model name for the related object"""
        if related_object_type := self.get_audit_log_related_object_type(
            history_instance
        ):
            return related_object_type.value
        else:
            return self._meta.verbose_name or self.__class__.__name__

    def _get_organisations(self, delta=None) -> typing.Iterable[Organisation] | None:
        """Return the related organisations for this model."""
        return None

    def _get_project(self, delta=None) -> Project | None:
        """Return the related project for this model."""
        return None

    def _get_environment(self, delta=None) -> Environment | None:
        """Return the related environment for this model."""
        return None


# TODO #2797 later: get IP address from request
def get_history_user(
    instance: typing.Any, request: HttpRequest
) -> typing.Optional["FFAdminUser"]:
    user = getattr(request, "user", None)
    return None if getattr(user, "is_master_api_key_user", False) else user


# TODO remove (some of) this once django-simple-history > 3.4.0 is released
# the rest should be contributed back to the project when possible
class HistoricalRecords(BaseHistoricalRecords):
    # apply merged patch https://github.com/jazzband/django-simple-history/pull/1218
    def create_historical_record_m2ms(self, history_instance, instance):
        for field in history_instance._history_m2m_fields:
            m2m_history_model = self.m2m_models[field]
            original_instance = history_instance.instance
            through_model = getattr(original_instance, field.name).through

            insert_rows = []

            # FIX IS HERE
            # `m2m_field_name()` is part of Django's internal API
            through_field_name = field.m2m_field_name()

            rows = through_model.objects.filter(**{through_field_name: instance})

            for row in rows:
                insert_row = {"history": history_instance}

                for through_model_field in through_model._meta.fields:
                    insert_row[through_model_field.name] = getattr(
                        row, through_model_field.name
                    )

                insert_rows.append(m2m_history_model(**insert_row))

            pre_create_historical_m2m_records.send(
                sender=m2m_history_model,
                rows=insert_rows,
                history_instance=history_instance,
                instance=instance,
                field=field,
            )
            created_rows = m2m_history_model.objects.bulk_create(insert_rows)
            post_create_historical_m2m_records.send(
                sender=m2m_history_model,
                created_rows=created_rows,
                history_instance=history_instance,
                instance=instance,
                field=field,
            )

    # apply merged patch https://github.com/jazzband/django-simple-history/pull/1243
    def get_m2m_fields_from_model(self, model):
        m2m_fields = set(self.m2m_fields)
        try:
            m2m_fields.update(getattr(model, self.m2m_fields_model_field_name))
        except AttributeError:
            pass
        # FIX IS HERE
        field_names = [
            field if isinstance(field, str) else field.name for field in m2m_fields
        ]
        return [getattr(model, field_name).field for field_name in field_names]

    # fix https://github.com/jazzband/django-simple-history/issues/1268
    # TODO create issue and PR applying this change to the superclass
    def create_historical_record(self, instance, history_type, using=None):
        using = using if self.use_base_model_db else None
        history_date = getattr(instance, "_history_date", timezone.now())
        history_user = self.get_history_user(instance)
        history_change_reason = self.get_change_reason_for_object(
            instance, history_type, using
        )
        manager = getattr(instance, self.manager_name)

        attrs = {}
        # FIX IS HERE
        for field in manager.model.tracked_fields:
            attrs[field.attname] = getattr(instance, field.attname)

        relation_field = getattr(manager.model, "history_relation", None)
        if relation_field is not None:
            attrs["history_relation"] = instance

        history_instance = manager.model(
            history_date=history_date,
            history_type=history_type,
            history_user=history_user,
            history_change_reason=history_change_reason,
            **attrs,
        )

        pre_create_historical_record.send(
            sender=manager.model,
            instance=instance,
            history_date=history_date,
            history_user=history_user,
            history_change_reason=history_change_reason,
            history_instance=history_instance,
            using=using,
        )

        history_instance.save(using=using)
        self.create_historical_record_m2ms(history_instance, instance)

        post_create_historical_record.send(
            sender=manager.model,
            instance=instance,
            history_instance=history_instance,
            history_date=history_date,
            history_user=history_user,
            history_change_reason=history_change_reason,
            using=using,
        )

    # fix: should check settings
    # TODO create issue and PR adding these changes to the superclass
    def m2m_changed(self, instance, action, attr, pk_set, reverse, **_):
        # FIX IS HERE
        if not getattr(settings, "SIMPLE_HISTORY_ENABLED", True):
            return
        super().m2m_changed(instance, action, attr, pk_set, reverse)

    # fix: m2m fields not tracked when through model used directly
    # TODO create issue and PR adding these changes to the superclass
    def finalize(self, sender, **kwargs):
        super().finalize(sender, **kwargs)

        # repeat sender check from superclass
        inherited = False
        if self.cls is not sender:  # set in concrete
            inherited = self.inherit and issubclass(sender, self.cls)
            if not inherited:
                return  # set in abstract

        # connect additional m2m signal handlers
        for field in self.get_m2m_fields_from_model(sender):
            models.signals.post_save.connect(
                functools.partial(
                    self.post_m2m_save_or_delete,
                    cls=sender,
                    attr=field.name,
                ),
                sender=field.remote_field.through,
                weak=False,
            )
            models.signals.post_delete.connect(
                functools.partial(
                    self.post_m2m_save_or_delete,
                    cls=sender,
                    attr=field.name,
                    created=False,  # unused but required to match post_save signature
                ),
                sender=field.remote_field.through,
                weak=False,
            )

    def post_m2m_save_or_delete(self, instance, created, cls, attr, **kwargs):
        # call post_save on parent model
        instance_attr = cls._meta.get_field(attr).m2m_field_name()
        self.post_save(getattr(instance, instance_attr), False, **kwargs)


def default_get_create_log_message(
    self: _AbstractBaseAuditableModel, history_instance
) -> str | None:
    return CREATED_MESSAGE.format(
        model_name=self.get_audit_log_model_name(history_instance),
        identity=self.get_audit_log_identity(),
    )


def _get_action(model: _AbstractBaseAuditableModel, field: str) -> str:
    new_value = getattr(model, field)
    if new_value is True:
        return "set true"
    if new_value is False:
        return "set false"
    if new_value is None:
        return "set null"

    return "updated"


def default_get_update_log_message(
    self: _AbstractBaseAuditableModel, history_instance, delta: ModelDelta
) -> str | None:
    if not history_instance.prev_record:
        logger.warning(f"No previous record for {self}")
        return None

    m2m_fields = {field.name: field for field in self.history.model._history_m2m_fields}
    model_name = self.get_audit_log_model_name(history_instance)
    identity = self.get_audit_log_identity()

    def describe(change: ModelChange) -> str:
        message = UPDATED_MESSAGE.format(
            model_name=model_name,
            identity=identity,
            field=change.field,
            action=_get_action(self, change.field),
        )

        if m2m_field := m2m_fields.get(change.field):

            def get_identity(pk):
                obj = m2m_field.related_model.objects.filter(pk=pk).first()
                # related model MUST implement get_audit_log_identity
                return obj.get_audit_log_identity() if obj else "None"

            reverse_field_name = m2m_field.m2m_reverse_field_name()
            old_values = {
                through[reverse_field_name]: through for through in change.old
            }
            new_values = {
                through[reverse_field_name]: through for through in change.new
            }
            for pk in new_values.keys() - old_values.keys():
                message += f"; added: {get_identity(pk)}"
            for pk in old_values.keys() - new_values.keys():
                message += f"; removed: {get_identity(pk)}"
            for pk in new_values.keys() & old_values.keys():
                related_identity = get_identity(pk)
                for field in old_values[pk].keys() | new_values[pk].keys():
                    if old_values[pk].get(field) != new_values[pk].get(field):
                        message += f"; {field} changed: {related_identity}"

        return message

    return "; ".join(describe(change) for change in delta.changes) or None


def default_get_delete_log_message(
    self: _AbstractBaseAuditableModel, history_instance
) -> str | None:
    return DELETED_MESSAGE.format(
        model_name=self.get_audit_log_model_name(history_instance),
        identity=self.get_audit_log_identity(),
    )


def abstract_base_auditable_model_factory(
    related_object_type: RelatedObjectType,
    unaudited_fields: typing.Sequence[str] | None = None,
    audited_m2m_fields: typing.Sequence[str] | None = None,
    audit_create=False,
    audit_update=False,
    audit_delete=False,
) -> typing.Type[_AbstractBaseAuditableModel]:
    class Base(_AbstractBaseAuditableModel):
        history = HistoricalRecords(
            bases=[BaseHistoricalModel],
            excluded_fields=unaudited_fields or (),
            m2m_fields=audited_m2m_fields or (),
            get_user=get_history_user,
            inherit=True,
        )

        class Meta:
            abstract = True

    Base.related_object_type = related_object_type
    if audit_create:
        Base.get_create_log_message = default_get_create_log_message
    if audit_update:
        Base.get_update_log_message = default_get_update_log_message
    if audit_delete:
        Base.get_delete_log_message = default_get_delete_log_message

    return Base


def register_auditable_model(
    model: type[models.Model],
    app: str,
    related_object_type: RelatedObjectType,
    unaudited_fields: typing.Sequence[str] | None = None,
    audited_m2m_fields: typing.Sequence[str] | None = None,
    *,
    audit_create=False,
    audit_update=False,
    audit_delete=False,
):
    register(
        model,
        app,
        bases=[BaseHistoricalModel],
        excluded_fields=unaudited_fields or (),
        m2m_fields=audited_m2m_fields or (),
        get_user=get_history_user,
    )

    for attr in _AbstractBaseAuditableModel.__dict__:
        try:
            getattr(model, attr)
        except AttributeError:
            setattr(model, attr, getattr(_AbstractBaseAuditableModel, attr))

    model.related_object_type = related_object_type
    if audit_create:
        model.get_create_log_message = default_get_create_log_message
    if audit_update:
        model.get_update_log_message = default_get_update_log_message
    if audit_delete:
        model.get_delete_log_message = default_get_delete_log_message
