from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from integrations.slack.models import SlackConfiguration, SlackEnvironment


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

        return SlackEnvironment.objects.create(
            **validated_data, slack_configuration=config
        )


class SlackChannelSerializer(serializers.Serializer):
    channel_name = serializers.CharField()
    channel_id = serializers.CharField()


class SlackChannelListSerializer(serializers.Serializer):
    cursor = serializers.CharField()
    channels = serializers.ListField(child=SlackChannelSerializer())


class SlackOauthInitQueryParamSerializer(serializers.Serializer):
    redirect_url = serializers.URLField(allow_blank=False)


class SlackChannelListQueryParamSerializer(serializers.Serializer):
    limit = serializers.IntegerField(default=20, max_value=1000, min_value=1)
    cursor = serializers.CharField(required=False)
