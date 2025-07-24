from typing import Any, Type

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model
from rest_framework import serializers

from metadata.models import (
    Metadata,
    MetadataField,
    MetadataModelField,
    MetadataModelFieldRequirement,
)
from metadata.types import MetadataItem
from organisations.models import Organisation
from projects.models import Project
from util.drf_writable_nested.serializers import (
    DeleteBeforeUpdateWritableNestedModelSerializer,
)


class MetadataFieldQuerySerializer(serializers.Serializer):  # type: ignore[type-arg]
    organisation = serializers.IntegerField(
        required=True, help_text="Organisation ID to filter by"
    )


class SupportedRequiredForModelQuerySerializer(serializers.Serializer):  # type: ignore[type-arg]
    model_name = serializers.CharField(required=True)


class MetadataFieldSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = MetadataField
        fields = ("id", "name", "type", "description", "organisation")


class MetadataModelFieldQuerySerializer(serializers.Serializer):  # type: ignore[type-arg]
    content_type = serializers.IntegerField(
        required=False, help_text="Content type of the model to filter by."
    )


class MetadataModelFieldRequirementSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = MetadataModelFieldRequirement
        fields = ("content_type", "object_id")


class MetaDataModelFieldSerializer(DeleteBeforeUpdateWritableNestedModelSerializer):
    is_required_for = MetadataModelFieldRequirementSerializer(many=True, required=False)

    class Meta:
        model = MetadataModelField
        fields = ("id", "field", "content_type", "is_required_for")

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        data = super().validate(data)
        for requirement in data.get("is_required_for", []):
            model_type = requirement["content_type"].model
            if model_type == "organisation":
                org_id = requirement["object_id"]
            elif model_type == "project":
                try:
                    org_id = (
                        requirement["content_type"]
                        .model_class()
                        .objects.get(id=requirement["object_id"])
                        .organisation_id
                    )
                except ObjectDoesNotExist:
                    raise serializers.ValidationError(
                        "The requirement organisation does not match the field organisation"
                    )
            else:
                raise serializers.ValidationError(
                    "The requirement content type must be project or organisation"
                )
            if org_id != data["field"].organisation_id:
                raise serializers.ValidationError(
                    "The requirement organisation does not match the field organisation"
                )
        return data


class ContentTypeSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = ContentType
        fields = ("id", "app_label", "model")


class MetadataSerializer(serializers.ModelSerializer[Metadata]):
    class Meta:
        model = Metadata
        fields = ("id", "model_field", "field_value")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        attrs = super().validate(attrs)
        if not attrs["model_field"].field.is_field_value_valid(attrs["field_value"]):
            raise serializers.ValidationError(
                f"Invalid value for field {attrs['model_field'].field.name}"
            )
        return attrs


class SerializerWithMetadata(serializers.Serializer):  # type: ignore[type-arg]
    """
    Add metadata functionality to a serializer

    TODO:
    - Improve class name. This is more of a mixin than a base class.
    - Avoid implicit method calling, e.g. from _get_required_for_object.
    """

    def _get_required_for_object(
        self,
        requirement: MetadataModelFieldRequirement,
        data: dict[str, Any],
    ) -> Model:
        model_name = requirement.content_type.model
        method_name = f"get_{model_name}"
        try:
            instance: Model = getattr(self, method_name)(data)
        except AttributeError:
            raise ValueError(f"`{method_name}` method does not exist")
        return instance

    def _validate_required_metadata(self, data: dict[str, Any]) -> None:
        metadata = data.get("metadata", [])
        content_type = ContentType.objects.get_for_model(self.Meta.model)
        organisation = self.get_organisation(data)
        requirements = MetadataModelFieldRequirement.objects.filter(
            model_field__content_type=content_type,
            model_field__field__organisation=organisation,
        )

        for requirement in requirements:
            required_for = self._get_required_for_object(requirement, data)
            if required_for.pk == requirement.object_id:
                if not any(
                    field["model_field"] == requirement.model_field
                    for field in metadata
                ):
                    raise serializers.ValidationError(
                        {
                            "metadata": f"Missing required metadata field: {requirement.model_field.field.name}"
                        }
                    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        attrs = super().validate(attrs)
        self._validate_required_metadata(attrs)
        return attrs

    def update_metadata(
        self,
        instance: Model,
        metadata_data: list[MetadataItem],
    ) -> None:
        content_type = ContentType.objects.get_for_model(instance.__class__)

        if not metadata_data:
            Metadata.objects.filter(
                object_id=instance.pk,
                content_type=content_type,
            ).delete()
            return

        incoming_updated_fields = {
            item["model_field"].id for item in metadata_data if not item.get("delete")
        }

        Metadata.objects.filter(
            object_id=instance.pk,
            content_type=content_type,
        ).exclude(
            model_field__id__in=incoming_updated_fields,
        ).delete()

        for metadata_item in metadata_data:
            metadata_model_field = metadata_item["model_field"]
            if metadata_model_field is not None and metadata_model_field.id is not None:
                Metadata.objects.update_or_create(
                    model_field=metadata_model_field,
                    content_type=content_type,
                    object_id=instance.pk,
                    defaults={
                        "field_value": metadata_item["field_value"],
                    },
                )

    # NOTE: Implicitly required by _validate_required_metadata
    def get_organisation(self, validated_data: dict[str, Any]) -> Organisation:
        return self.get_project(validated_data).organisation

    # NOTE: Implicitly required by _validate_required_metadata
    def get_project(self, validated_data: dict[str, Any]) -> Project:
        try:  # Attempt to find the project in the serializer context
            assert isinstance(project := self.context["project"], Project)
            return project
        except (KeyError, AssertionError):
            pass

        try:  # Attempt to retrieve the project from validated data
            assert isinstance(project := validated_data["project"], Project)
            return project
        except (KeyError, AssertionError):
            pass

        try:  # Attempt to obtain the project to which the object belongs
            assert isinstance(project := self.instance.project, Project)  # type: ignore[union-attr]
            return project
        except AttributeError:
            pass

        raise serializers.ValidationError(
            "Unable to retrieve project for metadata validation."
        )

    class Meta:
        model: Type[Model] = Model
