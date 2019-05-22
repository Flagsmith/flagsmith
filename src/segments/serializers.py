from rest_framework import serializers

from . import models


class SegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Segment
        fields = '__all__'
