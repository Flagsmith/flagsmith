from rest_framework import serializers

from permissions.models import PermissionModel


class PermissionModelSerializer(serializers.ModelSerializer):
    supports_tag = serializers.SerializerMethodField()

    class Meta:
        model = PermissionModel
        fields = ("key", "description", "supports_tag")

    def get_supports_tag(self, obj: PermissionModel) -> bool:
        return obj.key in self.context.get("tag_supported_permissions", [])


class CreateUpdateUserPermissionSerializerABC(serializers.ModelSerializer):
    class Meta:
        abstract = True
        fields = ("id", "permissions", "admin")
        read_only_fields = ("id",)

    def create(self, validated_data):
        permissions = validated_data.pop("permissions", [])
        instance = super(CreateUpdateUserPermissionSerializerABC, self).create(
            validated_data
        )
        instance.permissions.set(permissions)
        return instance

    def update(self, instance, validated_data):
        permissions = validated_data.pop("permissions", [])
        instance = super(CreateUpdateUserPermissionSerializerABC, self).update(
            instance, validated_data
        )
        instance.permissions.set(permissions)
        return instance


class UserObjectPermissionsSerializer(serializers.Serializer):
    permissions = serializers.ListField(child=serializers.CharField())
    admin = serializers.BooleanField()
