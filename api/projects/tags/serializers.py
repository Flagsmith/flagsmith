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
