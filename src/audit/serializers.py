from rest_framework import serializers

from audit.models import AuditLog
from users.serializers import UserListSerializer


class AuditLogSerializer(serializers.ModelSerializer):
    author = UserListSerializer()

    class Meta:
        model = AuditLog
        fields = ('created_date', 'log', 'author', 'related_object_id', 'related_object_type')
