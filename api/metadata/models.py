from core.models import AbstractBaseExportableModel
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from organisations.models import Organisation


class FieldType(models.TextChoices):
    INTEGER = "int"
    STRING = "str"
    BOOLEAN = "bool"
    FLOAT = "float"


class MetadataField(AbstractBaseExportableModel):
    name = models.CharField(max_length=255)
    type = models.CharField(
        max_length=255, choices=FieldType.choices, default=FieldType.STRING
    )
    description = models.TextField(blank=True, null=True)
    is_required = models.BooleanField(default=False)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)


class Metadata(AbstractBaseExportableModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    field = models.ForeignKey(MetadataField, on_delete=models.CASCADE)
    field_data = models.TextField()

    # TODO: index
