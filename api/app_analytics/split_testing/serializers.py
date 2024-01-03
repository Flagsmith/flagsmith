from rest_framework import serializers

from environments.identities.models import Identity
from features.multivariate.serializers import (
    NestedMultivariateFeatureOptionSerializer,
)
from features.serializers import FeatureSerializer

from .models import ConversionEvent, SplitTest


class ConversionEventSerializer(serializers.Serializer):
    identity_identifier = serializers.CharField(required=True)

    def save(self, *args, **kwargs) -> ConversionEvent:
        environment = self.context["request"].environment
        identity = Identity.objects.get(
            environment=environment,
            identifier=self.validated_data["identity_identifier"],
        )
        return ConversionEvent.objects.create(
            environment=environment,
            identity=identity,
        )


class SplitTestSerializer(serializers.ModelSerializer):
    feature = FeatureSerializer()
    multivariate_feature_option = NestedMultivariateFeatureOptionSerializer()

    class Meta:
        model = SplitTest
        fields = (
            "feature",
            "multivariate_feature_option",
            "evaluation_count",
            "conversion_count",
            "pvalue",
            "statistic",
        )
