import uuid

from django.db import models
from django.db.models import Manager


class AbstractBaseExportableModelManager(Manager):
    def get_by_natural_key(self, uuid_: str):
        return self.get(uuid=uuid_)


class AbstractBaseExportableModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)

    objects = AbstractBaseExportableModelManager()

    class Meta:
        abstract = True

    def natural_key(self):
        return str(self.uuid)
