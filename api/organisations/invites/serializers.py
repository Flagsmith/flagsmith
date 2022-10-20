from rest_framework import serializers

from organisations.invites.models import Invite, InviteLink
from users.serializers import UserListSerializer


class InviteLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = InviteLink
        fields = ("id", "hash", "date_created", "role", "expires_at")
        read_only_fields = ("id", "hash", "date_created")


class InviteListSerializer(serializers.ModelSerializer):
    invited_by = UserListSerializer()

    class Meta:
        model = Invite
        fields = ("id", "email", "date_created", "invited_by", "permission_groups")
