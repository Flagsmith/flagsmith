from rest_framework import serializers

from .models import Organisation


class InviteMixin:
    def _get_invited_by(self):
        return self.context.get("request").user if self.context.get("request") else None

    def _get_organisation(self):
        try:
            return Organisation.objects.get(pk=self.context.get("organisation"))
        except Organisation.DoesNotExist:
            raise serializers.ValidationError({"emails": "Invalid organisation."})
