from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from integrations.slack.models import SlackConfiguration, SlackEnvironment

from .exceptions import SlackChannelJoinError
from .slack import SlackWrapper


class SlackEnvironmentSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = SlackEnvironment
        fields = ("id", "channel_id", "enabled")

    def save(self, **kwargs):  # type: ignore[no-untyped-def]
        try:
            slack_configuration = SlackConfiguration.objects.get(
                project=kwargs.get("environment").project  # type: ignore[union-attr]
            )
        except ObjectDoesNotExist as e:
            raise serializers.ValidationError(
                "Slack api token not found. Please generate the token using oauth"
            ) from e
        kwargs.update(slack_configuration=slack_configuration)
        try:
            SlackWrapper(  # type: ignore[no-untyped-call]
                api_token=slack_configuration.api_token,
                channel_id=self.validated_data.get("channel_id"),
            ).join_channel()
        except SlackChannelJoinError as e:
            raise serializers.ValidationError(e) from e  # type: ignore[arg-type]
        return super().save(**kwargs)


class SlackChannelSerializer(serializers.Serializer):  # type: ignore[type-arg]
    channel_name = serializers.CharField()
    channel_id = serializers.CharField()


class SlackChannelListSerializer(serializers.Serializer):  # type: ignore[type-arg]
    cursor = serializers.CharField()
    channels = serializers.ListField(child=SlackChannelSerializer())


class SlackOauthInitQueryParamSerializer(serializers.Serializer):  # type: ignore[type-arg]
    redirect_url = serializers.URLField(allow_blank=False)


class SlackChannelListQueryParamSerializer(serializers.Serializer):  # type: ignore[type-arg]
    limit = serializers.IntegerField(default=20, max_value=1000, min_value=1)
    cursor = serializers.CharField(required=False)
