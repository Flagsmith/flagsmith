from rest_framework import serializers

from .models import ExternalResources, FeatureExternalResources


class ExternalResourcesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalResources
        fields = (
            "id",
            "url",
            "type",
            "project",
        )
        # read_only_fields = ("project",)

    # def validate(self, data):
    #     tags = data.get("tags", [])
    #     # If tags are selected, check that they from the same organization as the role.
    #     if tags:
    #         organisation_id = int(self.context["view"].kwargs["organisation_pk"])
    #         project_ids = Project.objects.filter(
    #             organisation__id=organisation_id
    #         ).values_list("id", flat=True)

    #         if any(tag.project_id not in project_ids for tag in tags):
    #             raise serializers.ValidationError(
    #                 {"tags": "At least one tag does not belong to this organisation"}
    #             )
    #     return data


class FeatureExternalResourcesSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureExternalResources
        fields = ("id", "feature", "external_resource")
        read_only_fields = ("external_resource",)

    # def validate(self, data):
    #     organisation_pk = int(self.context["view"].kwargs["organisation_pk"])

    #     if not data["user"].belongs_to(organisation_pk):
    #         raise serializers.ValidationError(
    #             {"user": "User does not belong to this organisation"}
    #         )
    #     return data
