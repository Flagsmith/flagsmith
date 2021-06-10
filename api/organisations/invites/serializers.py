from rest_framework import serializers

from organisations.invites.models import InviteLink


class InviteLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = InviteLink
        fields = ("id", "hash", "date_created", "role", "expires_at")
        read_only_fields = ("id", "hash", "date_created")
