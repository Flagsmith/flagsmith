from urllib.parse import urlparse

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from core.models import AbstractBaseExportableModel
from organisations.models import Organisation

from .fields import GenericObjectID

FIELD_VALUE_MAX_LENGTH = 2000

# A map of model name to a function that takes the object id and returns the organisation_id
SUPPORTED_REQUIREMENTS_MAPPING = {
    "environment": ["organisation", "project"],
    "feature": ["organisation", "project"],
    "segment": ["organisation", "project"],
}


class FieldType(models.TextChoices):
    INTEGER = "int"
    STRING = "str"
    BOOLEAN = "bool"
    URL = "url"
    MULTILINE_STRING = "multiline_str"


class MetadataField(AbstractBaseExportableModel):
    """This model represents a metadata field(specific to an organisation) that can be attached to any model"""

    name = models.CharField(max_length=255)
    type = models.CharField(
        max_length=255, choices=FieldType.choices, default=FieldType.STRING
    )
    description = models.TextField(blank=True, null=True)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)

    def is_field_value_valid(self, field_value: str) -> bool:
        if len(field_value) > FIELD_VALUE_MAX_LENGTH:
            return False
        return self.__getattribute__(f"validate_{self.type}")(field_value)  # type: ignore[no-any-return]

    def validate_int(self, field_value: str):  # type: ignore[no-untyped-def]
        try:
            int(field_value)
        except ValueError:
            return False
        return True

    def validate_bool(self, field_value: str):  # type: ignore[no-untyped-def]
        if field_value.lower() in ["true", "false"]:
            return True
        return False

    def validate_url(self, field_value: str):  # type: ignore[no-untyped-def]
        try:
            result = urlparse(field_value)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def validate_str(self, field_value: str):  # type: ignore[no-untyped-def]
        return True

    def validate_multiline_str(self, field_value: str):  # type: ignore[no-untyped-def]
        return True

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

    class Meta:
        unique_together = ("content_type", "object_id", "model_field")


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

    def deep_clone_for_new_entity(self, cloned_entity: models.Model) -> "Metadata":
        content_type = ContentType.objects.get_for_model(cloned_entity)
        metadata: Metadata = Metadata.objects.create(
            model_field=self.model_field,
            content_type=content_type,
            object_id=cloned_entity.pk,
            field_value=self.field_value,
        )
        return metadata
