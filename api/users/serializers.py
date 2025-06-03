import json
from datetime import datetime
from typing import Any

from djoser.serializers import (  # type: ignore[import-untyped]
    UserSerializer as DjoserUserSerializer,
)
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from organisations.models import Organisation
from organisations.serializers import UserOrganisationSerializer

from .models import (
    FFAdminUser,
    UserPermissionGroup,
    UserPermissionGroupMembership,
)


class UserIdSerializer(serializers.Serializer):  # type: ignore[type-arg]
    id = serializers.IntegerField()

    def update(self, instance, validated_data):  # type: ignore[no-untyped-def]
        pass

    def create(self, validated_data):  # type: ignore[no-untyped-def]
        organisation = Organisation.objects.get(pk=self.context.get("organisation"))
        user = self._get_user(validated_data)  # type: ignore[no-untyped-call]

        if user and organisation in user.organisations.all():
            user.remove_organisation(organisation)
        user.permission_groups.remove(
            *UserPermissionGroup.objects.filter(organisation=organisation)
        )

        return user

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if not FFAdminUser.objects.filter(pk=attrs.get("id")).exists():
            message = "User with id %d does not exist" % attrs.get("id")
            raise ValidationError({"id": message})
        return attrs

    def _get_user(self, validated_data):  # type: ignore[no-untyped-def]
        try:
            return FFAdminUser.objects.get(pk=validated_data.get("id"))
        except FFAdminUser.DoesNotExist:
            return None


class UserFullSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    organisations = UserOrganisationSerializer(source="userorganisation_set", many=True)

    class Meta:
        model = FFAdminUser
        fields = ("id", "email", "first_name", "last_name", "organisations", "uuid")


class UserLoginSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = FFAdminUser
        fields = ("email", "password")


class UserListSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    role = serializers.SerializerMethodField(read_only=True)
    join_date = serializers.SerializerMethodField(read_only=True)

    default_fields = ("id", "email", "first_name", "last_name", "last_login", "uuid")
    organisation_users_fields = (
        "role",
        "date_joined",
    )

    class Meta:
        model = FFAdminUser

    def get_field_names(self, declared_fields, info):  # type: ignore[no-untyped-def]
        fields = self.default_fields
        if self.context.get("organisation"):
            fields += self.organisation_users_fields  # type: ignore[assignment]
        return fields

    def get_role(self, instance):  # type: ignore[no-untyped-def]
        return instance.get_organisation_role(self.context.get("organisation"))

    def get_join_date(self, instance):  # type: ignore[no-untyped-def]
        return instance.get_organisation_join_date(self.context.get("organisation"))


class UserIdsSerializer(serializers.Serializer):  # type: ignore[type-arg]
    user_ids = serializers.ListField(child=serializers.IntegerField())

    def validate(self, data):  # type: ignore[no-untyped-def]
        if not FFAdminUser.objects.filter(id__in=data["user_ids"]).count() == len(
            data["user_ids"]
        ):
            raise serializers.ValidationError("Some users not found")

        return data


class UserPermissionGroupSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = UserPermissionGroup
        fields = ("id", "name", "users", "is_default", "external_id")
        read_only_fields = ("id",)


class UserPermissionGroupSummarySerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = UserPermissionGroup
        fields = ("id", "name")
        read_only_fields = ("id", "name")


class ListUserPermissionGroupMembershipSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
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


class UserPermissionGroupMembershipSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    group_admin = serializers.SerializerMethodField()

    class Meta:
        model = FFAdminUser
        fields = ("id", "email", "first_name", "last_name", "last_login", "group_admin")

    def get_group_admin(self, instance: FFAdminUser) -> bool:
        return instance.id in self.context.get("group_admins", [])


class UserPermissionGroupSerializerDetail(UserPermissionGroupSerializer):
    # TODO: remove users from here and just add a summary of number of users
    users = UserPermissionGroupMembershipSerializer(many=True, read_only=True)


class OnboardingToolsSerializer(serializers.Serializer[None]):
    completed = serializers.BooleanField(required=False, allow_null=True)
    integrations = serializers.ListField(
        child=serializers.CharField(), allow_empty=True, required=True
    )

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if data.get("completed") is None:
            data["completed"] = True
        return data


class OnboardingTaskSerializer(serializers.Serializer[None]):
    name = serializers.CharField()
    completed_at = serializers.DateTimeField(
        allow_null=True,
        required=False,
        default=lambda: datetime.now(),
    )

    def validate_completed_at(self, completed_at: datetime) -> datetime:
        return completed_at or datetime.now()


class PatchOnboardingSerializer(serializers.Serializer[None]):
    tasks = OnboardingTaskSerializer(many=True, required=False)
    tools = OnboardingToolsSerializer(required=False)

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if "tasks" not in data and "tools" not in data:
            raise serializers.ValidationError(
                "At least one of 'tasks' or 'tools' must be provided."
            )
        return data


class OnboardingResponseTypeSerializer(serializers.Serializer[None]):
    tasks = OnboardingTaskSerializer(many=True)
    tools = OnboardingToolsSerializer(required=False)


class CustomCurrentUserSerializer(DjoserUserSerializer):  # type: ignore[misc]
    auth_type = serializers.CharField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    uuid = serializers.UUIDField(read_only=True)

    def to_representation(self, instance: FFAdminUser) -> dict[str, Any]:
        rep = super().to_representation(instance)

        if instance.onboarding_data is not None:
            onboarding_json = json.loads(instance.onboarding_data)
        else:
            onboarding_json = None

        rep["onboarding"] = (
            OnboardingResponseTypeSerializer(onboarding_json).data
            if onboarding_json
            else None
        )
        return rep  # type: ignore[no-any-return]

    class Meta(DjoserUserSerializer.Meta):  # type: ignore[misc]
        fields = DjoserUserSerializer.Meta.fields + (
            "auth_type",
            "is_superuser",
            "date_joined",
            "uuid",
        )


class ListUsersQuerySerializer(serializers.Serializer):  # type: ignore[type-arg]
    exclude_current = serializers.BooleanField(default=False)
