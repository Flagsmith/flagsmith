from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from integrations.slack.models import SlackConfiguration, SlackEnvironment

from .slack import join_channel


class SlackEnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlackEnvironment
        fields = ("id", "channel_id", "enabled")

    def create(self, validated_data):
        try:
            config = SlackConfiguration.objects.get(
                project=validated_data["environment"].project
            )
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                "Slack api token not found. Please generate the token using oauth"
            )

        join_channel(config.api_token, validated_data["channel_id"])

        return SlackEnvironment.objects.create(
            **validated_data, slack_configuration=config
        )

    def update(self, instance, validated_data):
        join_channel(
            instance.slack_configuration.api_token, validated_data["channel_id"]
        )
        return super().update(instance, validated_data)


class SlackChannelListSerializer(serializers.Serializer):
    channel_name = serializers.CharField()
    channel_id = serializers.CharField()
