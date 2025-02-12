from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from organisations.models import Organisation
from organisations.serializers import UserOrganisationSerializer

from .models import (
    FFAdminUser,
    UserPermissionGroup,
    UserPermissionGroupMembership,
)


class UserIdSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        organisation = Organisation.objects.get(pk=self.context.get("organisation"))
        user = self._get_user(validated_data)

        if user and organisation in user.organisations.all():
            user.remove_organisation(organisation)
        user.permission_groups.remove(
            *UserPermissionGroup.objects.filter(organisation=organisation)
        )

        return user

    def validate(self, attrs):
        if not FFAdminUser.objects.filter(pk=attrs.get("id")).exists():
            message = "User with id %d does not exist" % attrs.get("id")
            raise ValidationError({"id": message})
        return attrs

    def _get_user(self, validated_data):
        try:
            return FFAdminUser.objects.get(pk=validated_data.get("id"))
        except FFAdminUser.DoesNotExist:
            return None


class UserFullSerializer(serializers.ModelSerializer):
    organisations = UserOrganisationSerializer(source="userorganisation_set", many=True)

    class Meta:
        model = FFAdminUser
        fields = ("id", "email", "first_name", "last_name", "organisations", "uuid")


class UserLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = FFAdminUser
        fields = ("email", "password")


class UserListSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField(read_only=True)
    join_date = serializers.SerializerMethodField(read_only=True)

    default_fields = ("id", "email", "first_name", "last_name", "last_login", "uuid")
    organisation_users_fields = (
        "role",
        "date_joined",
    )

    class Meta:
        model = FFAdminUser

    def get_field_names(self, declared_fields, info):
        fields = self.default_fields
        if self.context.get("organisation"):
            fields += self.organisation_users_fields
        return fields

    def get_role(self, instance):
        return instance.get_organisation_role(self.context.get("organisation"))

    def get_join_date(self, instance):
        return instance.get_organisation_join_date(self.context.get("organisation"))


class UserIdsSerializer(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.IntegerField())

    def validate(self, data):
        if not FFAdminUser.objects.filter(id__in=data["user_ids"]).count() == len(
            data["user_ids"]
        ):
            raise serializers.ValidationError("Some users not found")

        return data


class UserPermissionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPermissionGroup
        fields = ("id", "name", "users", "is_default", "external_id")
        read_only_fields = ("id",)


class UserPermissionGroupSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPermissionGroup
        fields = ("id", "name")
        read_only_fields = ("id", "name")


class ListUserPermissionGroupMembershipSerializer(serializers.ModelSerializer):
    # Note that in order to add the group_admin attribute, we use the UserPermissionGroupMembership
    # object instead of the FFAdminUser object. As such, we need to manually define the fields
    # and sources here.
    id = serializers.IntegerField(source="ffadminuser.id")
    email = serializers.EmailField(source="ffadminuser.email")
    first_name = serializers.CharField(source="ffadminuser.first_name")
    last_name = serializers.CharField(source="ffadminuser.last_name")
    last_login = serializers.CharField(source="ffadminuser.last_login")

    class Meta:
        model = UserPermissionGroupMembership
        fields = ("id", "email", "first_name", "last_name", "last_login", "group_admin")


class ListUserPermissionGroupSerializer(UserPermissionGroupSerializer):
    users = ListUserPermissionGroupMembershipSerializer(
        many=True, read_only=True, source="userpermissiongroupmembership_set"
    )


class UserPermissionGroupMembershipSerializer(serializers.ModelSerializer):
    group_admin = serializers.SerializerMethodField()

    class Meta:
        model = FFAdminUser
        fields = ("id", "email", "first_name", "last_name", "last_login", "group_admin")

    def get_group_admin(self, instance: FFAdminUser) -> bool:
        return instance.id in self.context.get("group_admins", [])


class UserPermissionGroupSerializerDetail(UserPermissionGroupSerializer):
    # TODO: remove users from here and just add a summary of number of users
    users = UserPermissionGroupMembershipSerializer(many=True, read_only=True)


class CustomCurrentUserSerializer(DjoserUserSerializer):
    auth_type = serializers.CharField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    uuid = serializers.UUIDField(read_only=True)

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + (
            "auth_type",
            "is_superuser",
            "date_joined",
            "uuid",
        )


class ListUsersQuerySerializer(serializers.Serializer):
    exclude_current = serializers.BooleanField(default=False)
