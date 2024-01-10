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
            "is_permanent",
            "is_system_tag",
        )
        read_only_fields = ("project", "is_system_tag")
