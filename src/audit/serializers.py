from rest_framework import serializers

from audit.models import AuditLog
from environments.serializers import EnvironmentSerializerLight
from projects.serializers import ProjectSerializer
from users.serializers import UserListSerializer


class AuditLogSerializer(serializers.ModelSerializer):
    author = UserListSerializer()
    environment = EnvironmentSerializerLight()
    project = ProjectSerializer()

    class Meta:
        model = AuditLog
        fields = ('created_date', 'log', 'author', 'environment', 'project', 'related_object_id', 'related_object_type')
