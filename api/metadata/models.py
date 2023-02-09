from core.models import AbstractBaseExportableModel
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from organisations.models import Organisation

from .fields import GenericObjectID

FIELD_VALUE_MAX_LENGTH = 2000

METADATA_SUPPORTED_MODELS = ["environment"]
REQUIRED_FOR_MODELS = {
    "environment": ["organisation", "project"],
}


class FieldType(models.TextChoices):
    INTEGER = "int"
    STRING = "str"
    BOOLEAN = "bool"
    FLOAT = "float"


class MetadataField(AbstractBaseExportableModel):
    """This model represents a metadata field(specific to an organisation) that can be attached to any model"""

    name = models.CharField(max_length=255)
    type = models.CharField(
        max_length=255, choices=FieldType.choices, default=FieldType.STRING
    )
    description = models.TextField(blank=True, null=True)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("name", "organisation")


class MetadataModelField(AbstractBaseExportableModel):
    """This model represents a metadata field that is attached to a specific model
    e.g: `Environment`
    """

    field = models.ForeignKey(MetadataField, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("field", "content_type")


class MetadataModelFieldRequirement(AbstractBaseExportableModel):
    """This model stores information about the requirement status of a `MetadataModelField` with respect to
    a parent object. e.g: if the `MetadataModelField` is attached to an `Environment` model,
    the parent object can be an instance of `Project` or `Organization`.
    """

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = GenericObjectID()
    content_object = GenericForeignKey("content_type", "object_id")
    model_field = models.ForeignKey(
        MetadataModelField, on_delete=models.CASCADE, related_name="is_required_for"
    )


class Metadata(AbstractBaseExportableModel):
    """This model represents the actual metadata attached to a specific instance of a model
    e.g: Environment.objects.get(id=1).metadata

    """

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = GenericObjectID()
    content_object = GenericForeignKey("content_type", "object_id")
    model_field = models.ForeignKey(MetadataModelField, on_delete=models.CASCADE)
    field_value = models.TextField(max_length=FIELD_VALUE_MAX_LENGTH)

    class Meta:
        unique_together = ("model_field", "content_type", "object_id")
