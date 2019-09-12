from rest_framework import serializers

from organisations.models import Subscription
from . import models


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        exclude = ('organisation',)


class OrganisationSerializer(serializers.ModelSerializer):
    num_seats = serializers.SerializerMethodField()

    # These fields are kept in for backwards compatibility with the FE for now,
    # will need to be removed in a future release in favour of nested subscription
    paid_subscription = serializers.SerializerMethodField()
    free_to_use_subscription = serializers.SerializerMethodField()
    subscription_date = serializers.SerializerMethodField()
    plan = serializers.SerializerMethodField()
    pending_cancellation = serializers.SerializerMethodField()

    subscription = SubscriptionSerializer(required=False)

    organisation_fields = ('id', 'name', 'created_date', 'webhook_notification_email', 'num_seats', 'subscription')
    subscription_fields = (
        'paid_subscription', 'free_to_use_subscription', 'subscription_date', 'plan', 'pending_cancellation')

    class Meta:
        model = models.Organisation

    def get_field_names(self, declared_fields, info):
        return self.organisation_fields + self.subscription_fields

    def to_internal_value(self, data):
        subscription_data = {}
        for field in self.subscription_fields:
            if data.get(field):
                subscription_data[field] = data.get(field)
        if subscription_data:
            data['subscription'] = subscription_data
        return super(OrganisationSerializer, self).to_internal_value(data)

    def create(self, validated_data):
        subscription_data = validated_data.pop('subscription')
        organisation = super(OrganisationSerializer, self).create(validated_data)
        Subscription.objects.create(organisation=organisation, **subscription_data)
        return organisation

    def get_num_seats(self, instance):
        return instance.users.count()

    def get_paid_subscription(self, instance):
        if hasattr(instance, 'subscription'):
            return instance.subscription.paid_subscription

    def get_free_to_use_subscription(self, instance):
        if hasattr(instance, 'subscription'):
            return instance.subscription.free_to_use_subscription

    def get_subscription_date(self, instance):
        if hasattr(instance, 'subscription'):
            return instance.subscription.subscription_date

    def get_plan(self, instance):
        if hasattr(instance, 'subscription'):
            return instance.subscription.plan

    def get_pending_cancellation(self, instance):
        if hasattr(instance, 'subscription'):
            return instance.subscription.pending_cancellation
