from copy import deepcopy

from rest_framework import serializers

from integrations.slack.models import SlackConfiguration, SlackEnvironment


class SlackEnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlackEnvironment
        fields = ("id", "channel_id", "enabled")

    def create(self, validated_data):
        data = deepcopy(validated_data)
        config = SlackConfiguration.objects.get(project=data["environment"].project)
        data.update({"slack_configuration": config})
        return SlackEnvironment.objects.create(**data)


class SlackChannelListSerializer(serializers.Serializer):
    channel_name = serializers.CharField()
    channel_id = serializers.CharField()
