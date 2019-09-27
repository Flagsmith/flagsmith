from rest_framework import serializers

from rest_framework import serializers

from users.models import Invite, FFAdminUser
from .models import Organisation, Subscription, UserOrganisation, OrganisationRole


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        exclude = ('organisation',)


class OrganisationSerializerFull(serializers.ModelSerializer):
    # These fields are kept in for backwards compatibility with the FE for now,
    # will need to be removed in a future release in favour of nested subscription
    paid_subscription = serializers.BooleanField(source='subscription.paid_subscription', required=False)
    free_to_use_subscription = serializers.BooleanField(source='subscription.free_to_use_subscription', required=False)
    subscription_date = serializers.DateField(source='subscription.subscription_date', required=False)
    plan = serializers.CharField(source='subscription.plan', required=False)
    pending_cancellation = serializers.BooleanField(source='subscription.pending_cancellation', required=False)

    subscription = SubscriptionSerializer(required=False)

    organisation_fields = (
        'id', 'name', 'created_date', 'webhook_notification_email', 'num_seats', 'subscription'
    )

    subscription_fields = (
        'paid_subscription', 'free_to_use_subscription', 'subscription_date', 'plan', 'pending_cancellation'
    )

    class Meta:
        model = Organisation

    def get_field_names(self, declared_fields, info):
        return self.organisation_fields + self.subscription_fields

    def to_internal_value(self, data):
        """
        Grab the subscription fields out of the posted data and correct the data to look as though they were passed as
        a nested subscription object. Note that this assumes use of one OR the other - if fields are passed in both
        ways then those fields in the root subscription object will be ignored.
        """
        if not data.get('subscription'):
            subscription_data = {}
            for field in self.subscription_fields:
                if data.get(field):
                    subscription_data[field] = data.get(field)
            if subscription_data:
                data['subscription'] = subscription_data
        return super(OrganisationSerializerFull, self).to_internal_value(data)

    def create(self, validated_data):
        subscription_data = validated_data.pop('subscription', {})
        organisation = super(OrganisationSerializerFull, self).create(validated_data)
        Subscription.objects.create(organisation=organisation, **subscription_data)
        return organisation

    def update(self, instance, validated_data):
        subscription_data = validated_data.pop('subscription', {})
        self._update_subscription(instance, subscription_data)
        return super(OrganisationSerializerFull, self).update(instance, validated_data)

    def _update_subscription(self, organisation, subscription_data):
        subscription, _ = Subscription.objects.get_or_create(organisation=organisation)
        for key, value in subscription_data.items():
            setattr(subscription, key, value)
        subscription.save()


class OrganisationSerializerBasic(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ('id', 'name')


class UserOrganisationSerializer(serializers.ModelSerializer):
    organisation = OrganisationSerializerBasic(read_only=True)

    class Meta:
        model = UserOrganisation
        fields = ('role', 'organisation')


class InviteSerializerFull(serializers.ModelSerializer):
    class InvitedBySerializer(serializers.ModelSerializer):
        class Meta:
            model = FFAdminUser
            fields = ('id', 'email', 'first_name', 'last_name')

    invited_by = InvitedBySerializer()

    class Meta:
        model = Invite
        fields = ('id', 'email', 'role', 'date_created', 'invited_by')


class InviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invite
        fields = ('id', 'email', 'role', 'date_created')
        read_only_fields = ('id', 'date_created')

    def validate(self, attrs):
        if Invite.objects.filter(email=attrs['email'], organisation__id=self.context.get('organisation')).exists():
            raise serializers.ValidationError({'email': 'Invite for email %s already exists' % attrs['email']})
        return super(InviteSerializer, self).validate(attrs)


class MultiInvitesSerializer(serializers.Serializer):
    invites = InviteSerializer(many=True, required=False)
    frontend_base_url = serializers.CharField()
    emails = serializers.ListSerializer(child=serializers.EmailField(), required=False)

    def create(self, validated_data):
        organisation = self._get_organisation()
        user = self._get_invited_by()

        invites = validated_data.get('invites', [])

        # for backwards compatibility, allow emails to be sent as a list of strings still
        for email in validated_data.get('emails', []):
            invites.append({
                'email': email,
                'role': OrganisationRole.USER.name
            })

        created_invites = []
        for invite in invites:
            data = {
                **invite,
                'invited_by': user,
                'organisation': organisation,
                'frontend_base_url': validated_data['frontend_base_url']
            }
            created_invites.append(Invite.objects.create(**data))

        # return the created_invites to serialize the data back to the front end
        return created_invites

    def to_representation(self, instance):
        # Return the invites in a dictionary since the serializer expects a single instance to be returned, not a list
        return {
            'invites': [InviteSerializerFull(invite).data for invite in instance]
        }

    def validate(self, attrs):
        for email in attrs.get('emails', []):
            if Invite.objects.filter(email=email, organisation__id=self.context.get('organisation')).exists():
                raise serializers.ValidationError({'emails': 'Invite for email %s already exists' % email})
        return super(MultiInvitesSerializer, self).validate(attrs)

    def _get_invited_by(self):
        return self.context.get('request').user if self.context.get('request') else None

    def _get_organisation(self):
        try:
            return Organisation.objects.get(pk=self.context.get('organisation'))
        except Organisation.DoesNotExist:
            raise serializers.ValidationError({'emails': 'Invalid organisation.'})
