from projects.tags.models import Tag
from rest_framework import serializers


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'label', 'color', 'description', 'project')
        read_only_fields = ('project',)
