from typing import Any

from rest_framework import serializers

from projects.tags.models import Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            "id",
            "label",
            "color",
            "description",
            "project",
            "uuid",
            "is_permanent",
            "is_system_tag",
            "type",
        )
        read_only_fields = ("project", "uuid", "is_system_tag", "type")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if self.instance and self.instance.is_system_tag:
            raise serializers.ValidationError("Cannot update a system tag.")
        return super().validate(attrs)
