import pytest
from core.constants import STRING

from features.models import FeatureState
from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)
from features.serializers import FeatureStateSerializerBasic


@pytest.mark.parametrize(
    "percentage_value, expected_is_valid", ((90, True), (100, True), (110, False))
)
def test_feature_state_serializer_basic_validates_mv_percentage_values(
    feature, environment, percentage_value, expected_is_valid
):
    # Given
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)

    mv_feature_option = MultivariateFeatureOption.objects.create(
        feature=feature,
        type=STRING,
        string_value="foo",
        default_percentage_allocation=0,
    )
    mv_feature_state_value = MultivariateFeatureStateValue.objects.get(
        multivariate_feature_option=mv_feature_option
    )

    data = {
        "id": feature_state.id,
        "feature": feature.id,
        "environment": environment.id,
        "multivariate_feature_state_values": [
            {
                "id": mv_feature_state_value.id,
                "multivariate_feature_option": mv_feature_option.id,
                "percentage_allocation": percentage_value,
            }
        ],
    }
    serializer = FeatureStateSerializerBasic(instance=feature_state, data=data)

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid == expected_is_valid
