from rest_framework import serializers

from . import models


class OrganisationSerializer(serializers.ModelSerializer):
    num_seats = serializers.SerializerMethodField()

    class Meta:
        model = models.Organisation
        fields = ('id', 'name', 'created_date', 'webhook_notification_email', 'paid_subscription',
                  'free_to_use_subscription', 'subscription_date', 'plan', 'pending_cancellation', 'num_seats')

    def get_num_seats(self, instance):
        return instance.users.count()

