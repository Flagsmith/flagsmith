from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from integrations.slack.models import SlackConfiguration, SlackEnvironment

from .exceptions import SlackChannelJoinError
from .slack import SlackWrapper


class SlackEnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlackEnvironment
        fields = ("id", "channel_id", "enabled")

    def save(self, **kwargs):
        try:
            slack_configuration = SlackConfiguration.objects.get(
                project=kwargs.get("environment").project
            )
        except ObjectDoesNotExist as e:
            raise serializers.ValidationError(
                "Slack api token not found. Please generate the token using oauth"
            ) from e
        kwargs.update(slack_configuration=slack_configuration)
        try:
            SlackWrapper(
                api_token=slack_configuration.api_token,
                channel_id=self.validated_data.get("channel_id"),
            ).join_channel()
        except SlackChannelJoinError as e:
            raise serializers.ValidationError(e) from e
        return super().save(**kwargs)


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
