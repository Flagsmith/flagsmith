import logging
import typing
import uuid

from django.db import models
from django.db.models import Manager
from simple_history.models import HistoricalRecords

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


class BaseHistoricalModel(models.Model):
    include_in_audit = True

    master_api_key = models.ForeignKey(
        "api_keys.MasterAPIKey", blank=True, null=True, on_delete=models.DO_NOTHING
    )

    class Meta:
        abstract = True


class AbstractBaseAuditableModel(models.Model):
    # TODO: can we make excluded fields dynamic?
    history = HistoricalRecords(
        bases=[BaseHistoricalModel], excluded_fields=["uuid"], inherit=True
    )

    history_record_class_path = None
    related_object_type = None

    class Meta:
        abstract = True

    def get_create_log_message(self, history_instance) -> typing.Optional[str]:
        return None

    def get_update_log_message(self, history_instance) -> typing.Optional[str]:
        return None

    def get_delete_log_message(self, history_instance) -> typing.Optional[str]:
        return None

    def get_environment_and_project(
        self,
    ) -> typing.Tuple[typing.Optional["Environment"], typing.Optional["Project"]]:
        environment, project = self._get_environment(), self._get_project()
        if not (environment or project):
            raise Exception(
                "class should implement at least one of _get_environment or _get_project"
            )  # TODO: better exception
        return environment, project

    def get_extra_audit_log_kwargs(self, history_instance) -> dict:
        return {}

    def get_audit_log_author(self, history_instance) -> typing.Optional["FFAdminUser"]:
        return None

    def get_audit_log_related_object_id(self, history_instance) -> typing.Optional[int]:
        return self.id

    def get_audit_log_related_object_type(self, history_instance) -> RelatedObjectType:
        return self.related_object_type

    def _get_environment(self) -> typing.Optional["Environment"]:
        return None

    def _get_project(self) -> typing.Optional["Project"]:
        return None
