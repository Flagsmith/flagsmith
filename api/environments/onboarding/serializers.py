from typing import get_args

from rest_framework import serializers

from app_analytics.types import KnownSDK
from environments.models import Environment


class EnvironmentOnboardingStatusSerializer(serializers.ModelSerializer[Environment]):
    class Meta:
        model = Environment
        fields = ("first_evaluated_at", "first_evaluated_sdk_label")


class EnvironmentOnboardingStatusUpdateSerializer(serializers.Serializer[None]):
    first_evaluated_sdk_label = serializers.ChoiceField(choices=get_args(KnownSDK))
