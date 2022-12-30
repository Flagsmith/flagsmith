from core.models import AbstractBaseExportableModel
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from organisations.models import Organisation

FIELD_DATA_MAX_LENGTH = 2000


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
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)


class MetadataModelField(AbstractBaseExportableModel):
    field = models.ForeignKey(MetadataField, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    is_required = models.BooleanField(default=False)

    class Meta:
        unique_together = ("field", "content_type")


class Metadata(AbstractBaseExportableModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    model_field = models.ForeignKey(MetadataModelField, on_delete=models.CASCADE)
    field_data = models.TextField(max_length=FIELD_DATA_MAX_LENGTH)

    class Meta:
        unique_together = ("model_field", "content_type", "object_id")
