from rest_framework import serializers

from . import constants


class UsageDataSerializer(serializers.Serializer):
    flags = serializers.IntegerField()
    identities = serializers.IntegerField()
    traits = serializers.IntegerField()
    environment_document = serializers.IntegerField()
    day = serializers.CharField()


class UsageDataQuerySerializer(serializers.Serializer):
    project_id = serializers.IntegerField(required=False)
    environment_id = serializers.IntegerField(required=False)
    period = serializers.RegexField(
        regex=r"^(%s)$"
        % "|".join(
            [
                constants.CURRENT_BILLING_PERIOD,
                constants.PREVIOUS_BILLING_PERIOD,
                constants._90_DAY_PERIOD,
            ]
        ),
        required=False,
    )


class UsageTotalCountSerializer(serializers.Serializer):
    count = serializers.IntegerField()


class SDKAnalyticsFlagsSerializerDetail(serializers.Serializer):
    feature_name = serializers.CharField()
    identity_identifier = serializers.CharField(required=False, default=None)
    enabled_when_evaluated = serializers.BooleanField()
    count = serializers.IntegerField()


class SDKAnalyticsFlagsSerializer(serializers.Serializer):
    evaluations = SDKAnalyticsFlagsSerializerDetail(many=True)
