import typing

from django.db.models import Model
from rest_framework.serializers import ModelSerializer


class _BaseIntegrationModelSerializer(ModelSerializer):  # type: ignore[type-arg]
    one_to_one_field_name = None

    def create(self, validated_data):  # type: ignore[no-untyped-def]
        if existing_obj := self._get_existing_integration_model_obj(validated_data):
            existing_obj.deleted_at = None  # type: ignore[attr-defined]
            return self.update(instance=existing_obj, validated_data=validated_data)
        return super().create(validated_data)

    def _get_existing_integration_model_obj(
        self, validated_data: dict  # type: ignore[type-arg]
    ) -> typing.Optional[Model]:
        """
        Get the existing integration model (e.g. MixpanelConfig) for the given one-to-one related
        model (e.g. Environment) if one exists.
        """
        one_to_one_related_obj = validated_data.get(self.one_to_one_field_name)
        return (  # type: ignore[no-any-return]
            self.Meta.model.objects.all_with_deleted()  # type: ignore[attr-defined]
            .filter(**{self.one_to_one_field_name: one_to_one_related_obj})
            .first()
        )


class BaseEnvironmentIntegrationModelSerializer(_BaseIntegrationModelSerializer):
    one_to_one_field_name = "environment"  # type: ignore[assignment]


class BaseProjectIntegrationModelSerializer(_BaseIntegrationModelSerializer):
    one_to_one_field_name = "project_id"  # type: ignore[assignment]


class BaseOrganisationIntegrationModelSerializer(_BaseIntegrationModelSerializer):
    one_to_one_field_name = "organisation_id"  # type: ignore[assignment]
