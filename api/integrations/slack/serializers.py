from rest_framework import serializers

from integrations.slack.models import SlackConfiguration, SlackEnvironment


class SlackEnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlackEnvironment
        fields = ("channel_id", "environment", "enabled")


class SlackChannelListSerializer(serializers.Serializer):
    channel_name = serializers.CharField()
    channel_id = serializers.CharField()


# class SlackConfigurationSerializer(serializers.ModelSerializer):
#     environments = SlackEnvironmentSerializer(many=True, required=True)

#     class Meta:
#         model = SlackConfiguration
#         fields = ("id", "api_token", "channel_id", "environments")
