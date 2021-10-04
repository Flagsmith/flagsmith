import logging

from django.conf import settings
from rest_framework import serializers

from organisations.chargebee import get_subscription_data_from_hosted_page
from organisations.invites.models import Invite
from users.models import FFAdminUser

from .models import (
    Organisation,
    OrganisationRole,
    OrganisationWebhook,
    Subscription,
    UserOrganisation,
)

logger = logging.getLogger(__name__)


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        exclude = ("organisation",)


class OrganisationSerializerFull(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(required=False)
    role = serializers.SerializerMethodField()

    class Meta:
        model = Organisation
        fields = (
            "id",
            "name",
            "created_date",
            "webhook_notification_email",
            "num_seats",
            "subscription",
            "role",
            "persist_trait_data",
            "block_access_to_admin",
            "only_admin_can_create_project",
        )
        read_only_fields = (
            "id",
            "created_date",
            "num_seats",
            "role",
            "persist_trait_data",
            "block_access_to_admin",
        )

    def get_role(self, instance):
        if self.context.get("request"):
            user = self.context["request"].user
            return user.get_organisation_role(instance)


class OrganisationSerializerBasic(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ("id", "name")


class UserOrganisationSerializer(serializers.ModelSerializer):
    organisation = OrganisationSerializerBasic(read_only=True)

    class Meta:
        model = UserOrganisation
        fields = ("role", "organisation")


class InviteSerializerFull(serializers.ModelSerializer):
    class InvitedBySerializer(serializers.ModelSerializer):
        class Meta:
            model = FFAdminUser
            fields = ("id", "email", "first_name", "last_name")

    invited_by = InvitedBySerializer()

    class Meta:
        model = Invite
        fields = ("id", "email", "role", "date_created", "invited_by")


class InviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invite
        fields = ("id", "email", "role", "date_created")
        read_only_fields = ("id", "date_created")

    def validate(self, attrs):
        if Invite.objects.filter(
            email=attrs["email"], organisation__id=self.context.get("organisation")
        ).exists():
            raise serializers.ValidationError(
                {"email": "Invite for email %s already exists" % attrs["email"]}
            )
        return super(InviteSerializer, self).validate(attrs)


class MultiInvitesSerializer(serializers.Serializer):
    invites = InviteSerializer(many=True, required=False)
    frontend_base_url = serializers.CharField()
    emails = serializers.ListSerializer(child=serializers.EmailField(), required=False)

    def create(self, validated_data):
        organisation = self._get_organisation()
        user = self._get_invited_by()

        invites = validated_data.get("invites", [])

        # for backwards compatibility, allow emails to be sent as a list of strings still
        for email in validated_data.get("emails", []):
            invites.append({"email": email, "role": OrganisationRole.USER.name})

        created_invites = []
        for invite in invites:
            data = {
                **invite,
                "invited_by": user,
                "organisation": organisation,
                "frontend_base_url": validated_data["frontend_base_url"],
            }
            created_invites.append(Invite.objects.create(**data))

        # return the created_invites to serialize the data back to the front end
        return created_invites

    def to_representation(self, instance):
        # Return the invites in a dictionary since the serializer expects a single instance to be returned, not a list
        return {"invites": [InviteSerializerFull(invite).data for invite in instance]}

    def validate(self, attrs):
        for email in attrs.get("emails", []):
            if Invite.objects.filter(
                email=email, organisation__id=self.context.get("organisation")
            ).exists():
                raise serializers.ValidationError(
                    {"emails": "Invite for email %s already exists" % email}
                )
        return super(MultiInvitesSerializer, self).validate(attrs)

    def _get_invited_by(self):
        return self.context.get("request").user if self.context.get("request") else None

    def _get_organisation(self):
        try:
            return Organisation.objects.get(pk=self.context.get("organisation"))
        except Organisation.DoesNotExist:
            raise serializers.ValidationError({"emails": "Invalid organisation."})


class UpdateSubscriptionSerializer(serializers.Serializer):
    hosted_page_id = serializers.CharField()

    def create(self, validated_data):
        """
        Get the subscription data from Chargebee hosted page and store in the subscription
        """
        organisation = self._get_organisation()

        if settings.ENABLE_CHARGEBEE:
            subscription_data = get_subscription_data_from_hosted_page(
                hosted_page_id=validated_data["hosted_page_id"]
            )

            if subscription_data:
                Subscription.objects.update_or_create(
                    organisation=organisation, defaults=subscription_data
                )
            else:
                raise serializers.ValidationError(
                    {
                        "detail": "Couldn't get subscription information from hosted page."
                    }
                )
        else:
            logger.warning("Chargebee not configured. Not verifying hosted page.")

        return organisation

    def update(self, instance, validated_data):
        pass

    def _get_organisation(self):
        try:
            return Organisation.objects.get(pk=self.context.get("organisation"))
        except Organisation.DoesNotExist:
            raise serializers.ValidationError("Invalid organisation.")


class PortalUrlSerializer(serializers.Serializer):
    url = serializers.URLField()


class OrganisationWebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationWebhook
        fields = ("id", "url", "enabled")
        read_only_fields = ("id",)


class InfluxDataSerializer(serializers.Serializer):
    # todo this have to be changed after moving influxdb_wrapper to marshmallow
    events_list = serializers.ListSerializer(child=serializers.DictField())
