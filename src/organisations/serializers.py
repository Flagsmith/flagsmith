from rest_framework import serializers

from organisations.chargebee import get_subscription_data_from_hosted_page
from users.models import Invite
from .models import Organisation, Subscription, UserOrganisation, OrganisationRole


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        exclude = ('organisation',)


class OrganisationSerializerFull(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(required=False)

    class Meta:
        model = Organisation
        fields = ('id', 'name', 'created_date', 'webhook_notification_email', 'num_seats', 'subscription')


class OrganisationSerializerBasic(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ('id', 'name')


class UserOrganisationSerializer(serializers.ModelSerializer):
    organisation = OrganisationSerializerBasic(read_only=True)

    class Meta:
        model = UserOrganisation
        fields = ('role', 'organisation')


class InviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invite
        fields = ('email', 'role')

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

        for invite in invites:
            data = {
                **invite,
                'invited_by': user,
                'organisation': organisation,
                'frontend_base_url': validated_data['frontend_base_url']
            }
            Invite.objects.create(**data)

        # return the organisation to avoid rest framework error complaining that save should return an object
        return organisation

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


class UpdateSubscriptionSerializer(serializers.Serializer):
    hosted_page_id = serializers.CharField()

    def create(self, validated_data):
        """
        Get the subscription data from Chargebee hosted page and store in the subscription
        """
        organisation = self._get_organisation()
        subscription_data = get_subscription_data_from_hosted_page(hosted_page_id=validated_data['hosted_page_id'])

        if subscription_data:
            Subscription.objects.update_or_create(organisation=organisation, defaults=subscription_data)
        else:
            raise serializers.ValidationError({'detail': 'Couldn\'t get subscription information from hosted page.'})

        return organisation

    def update(self, instance, validated_data):
        pass

    def _get_organisation(self):
        try:
            return Organisation.objects.get(pk=self.context.get('organisation'))
        except Organisation.DoesNotExist:
            raise serializers.ValidationError('Invalid organisation.')
