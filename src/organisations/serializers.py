from rest_framework import serializers

from . import models


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Organisation
        fields = ('id', 'name', 'created_date', 'webhook_notification_email', 'paid_subscription',
        'free_to_use_subscription', 'subscription_date')
