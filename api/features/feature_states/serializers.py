from rest_framework import serializers


class FeatureValueSerializer(serializers.Serializer):  # type: ignore[type-arg]
    type = serializers.ChoiceField(
        choices=["integer", "string", "boolean"], required=True
    )
    value = serializers.CharField(required=True, allow_blank=True)

    def validate(self, data: dict) -> dict:  # type: ignore[type-arg]
        value_type = data["type"]
        string_val = data["value"]

        if value_type == "integer":
            try:
                int(string_val)
            except ValueError:
                raise serializers.ValidationError(
                    f"'{string_val}' is not a valid integer"
                )
        elif value_type == "boolean":
            if string_val.lower() not in ("true", "false"):
                raise serializers.ValidationError(
                    f"'{string_val}' is not a valid boolean (use 'true' or 'false')"
                )

        return data


class MultivariateValueSerializer(serializers.Serializer):  # type: ignore[type-arg]
    multivariate_feature_option = serializers.IntegerField(required=True)
    percentage_allocation = serializers.FloatField(
        required=True, min_value=0, max_value=100
    )
