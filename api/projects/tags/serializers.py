from rest_framework import serializers

from projects.tags.models import Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "label", "color", "description", "project")
        read_only_fields = ("project",)
