from rest_framework import serializers

from permissions.models import PermissionModel


class PermissionModelSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    supports_tag = serializers.SerializerMethodField()

    class Meta:
        model = PermissionModel
        fields = ("key", "description", "supports_tag")

    def get_supports_tag(self, obj: PermissionModel) -> bool:
        return obj.key in self.context.get("tag_supported_permissions", [])


class CreateUpdateUserPermissionSerializerABC(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        abstract = True
        fields = ("id", "permissions", "admin")
        read_only_fields = ("id",)

    def create(self, validated_data):  # type: ignore[no-untyped-def]
        permissions = validated_data.pop("permissions", [])
        instance = super(CreateUpdateUserPermissionSerializerABC, self).create(
            validated_data
        )
        instance.permissions.set(permissions)
        return instance

    def update(self, instance, validated_data):  # type: ignore[no-untyped-def]
        permissions = validated_data.pop("permissions", [])
        instance = super(CreateUpdateUserPermissionSerializerABC, self).update(
            instance, validated_data
        )
        instance.permissions.set(permissions)
        return instance


class TagBasedPermissionSerializer(serializers.Serializer):  # type: ignore[type-arg]
    permissions = serializers.ListField(child=serializers.CharField())
    tags = serializers.ListField(child=serializers.IntegerField())


class UserObjectPermissionsSerializer(serializers.Serializer):  # type: ignore[type-arg]
    permissions = serializers.ListField(child=serializers.CharField())
    admin = serializers.BooleanField()
    tag_based_permissions = TagBasedPermissionSerializer(many=True)
