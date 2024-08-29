import typing

from django.db.models import Model
from rest_framework.serializers import ModelSerializer


class _BaseIntegrationModelSerializer(ModelSerializer):
    one_to_one_field_name = None

    def create(self, validated_data):
        if existing_obj := self._get_existing_integration_model_obj(validated_data):
            existing_obj.deleted_at = None
            return self.update(instance=existing_obj, validated_data=validated_data)
        return super().create(validated_data)

    def _get_existing_integration_model_obj(
        self, validated_data: dict
    ) -> typing.Optional[Model]:
        """
        Get the existing integration model (e.g. MixpanelConfig) for the given one-to-one related
        model (e.g. Environment) if one exists.
        """
        one_to_one_related_obj = validated_data.get(self.one_to_one_field_name)
        return (
            self.Meta.model.objects.all_with_deleted()
            .filter(**{self.one_to_one_field_name: one_to_one_related_obj})
            .first()
        )


class BaseEnvironmentIntegrationModelSerializer(_BaseIntegrationModelSerializer):
    one_to_one_field_name = "environment"


class BaseProjectIntegrationModelSerializer(_BaseIntegrationModelSerializer):
    one_to_one_field_name = "project_id"


class BaseOrganisationIntegrationModelSerializer(_BaseIntegrationModelSerializer):
    one_to_one_field_name = "organisation_id"
