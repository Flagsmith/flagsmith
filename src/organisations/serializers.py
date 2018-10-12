from rest_framework import serializers

from . import models


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Organisation
        fields = ('id', 'name', 'created_date', 'webhook_notification_email')
