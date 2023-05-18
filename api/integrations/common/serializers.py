from rest_framework.serializers import ModelSerializer


class _BaseIntegrationModelSerializer(ModelSerializer):
    one_to_one_field_name = None

    def create(self, validated_data):
        if (related_obj := validated_data.get(self.one_to_one_field_name)) and (
            existing_obj := self.Meta.model.objects.all_with_deleted()
            .filter(**{self.one_to_one_field_name: related_obj})
            .first()
        ):
            existing_obj.deleted_at = None
            return self.update(instance=existing_obj, validated_data=validated_data)
        return super().create(validated_data)


class BaseEnvironmentIntegrationModelSerializer(_BaseIntegrationModelSerializer):
    one_to_one_field_name = "environment"


class BaseProjectIntegrationModelSerializer(_BaseIntegrationModelSerializer):
    one_to_one_field_name = "project"
