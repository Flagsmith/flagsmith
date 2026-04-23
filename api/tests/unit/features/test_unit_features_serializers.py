import pytest

from core.constants import BOOLEAN, INTEGER, STRING
from environments.models import Environment
from features.models import Feature, FeatureState
from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)
from features.multivariate.serializers import (
    FeatureMVOptionsValuesResponseSerializer,
    MultivariateOptionValuesSerializer,
)
from features.serializers import FeatureStateSerializerBasic


def test_feature_state_serializer_basic__null_environment_no_context__returns_validation_error(  # type: ignore[no-untyped-def]
    feature, environment
):
    # Given - null environment in payload and no environment in context
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)
    data = {
        "id": feature_state.id,
        "feature": feature.id,
        "environment": None,
    }
    serializer = FeatureStateSerializerBasic(
        instance=feature_state,
        data=data,
        context={},
    )

    # When
    is_valid = serializer.is_valid()

    # Then - should reject null environment, not raise AttributeError
    assert not is_valid
    assert "environment" in serializer.errors


def test_feature_state_serializer_basic__null_environment_with_context__falls_back_to_context(  # type: ignore[no-untyped-def]
    feature, environment
):
    # Given - null environment in payload but valid environment in context
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)
    data = {
        "id": feature_state.id,
        "feature": feature.id,
        "environment": None,
    }
    serializer = FeatureStateSerializerBasic(
        instance=feature_state,
        data=data,
        context={"environment": environment},
    )

    # When
    is_valid = serializer.is_valid()

    # Then - should fall back to context environment
    assert is_valid


@pytest.mark.parametrize(
    "percentage_value, expected_is_valid", ((90, True), (100, True), (110, False))
)
def test_feature_state_serializer_basic__mv_percentage_values__validates_correctly(  # type: ignore[no-untyped-def]
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


def test_multivariate_option_values_serializer__string_value__returns_string(
    multivariate_feature: MultivariateFeatureOption,
) -> None:
    # Given
    option = multivariate_feature.multivariate_options.first()

    # When
    serializer = MultivariateOptionValuesSerializer(option)

    # Then
    assert serializer.data["value"] == option.string_value


def test_multivariate_option_values_serializer__boolean_value__returns_boolean(
    feature: Feature,
) -> None:
    # Given
    option = MultivariateFeatureOption.objects.create(
        feature=feature,
        type=BOOLEAN,
        boolean_value=True,
        default_percentage_allocation=50,
    )

    # When
    serializer = MultivariateOptionValuesSerializer(option)

    # Then
    assert serializer.data["value"] is True


def test_multivariate_option_values_serializer__integer_value__returns_integer(
    feature: Feature,
) -> None:
    # Given
    option = MultivariateFeatureOption.objects.create(
        feature=feature,
        type=INTEGER,
        integer_value=42,
        default_percentage_allocation=50,
    )

    # When
    serializer = MultivariateOptionValuesSerializer(option)

    # Then
    assert serializer.data["value"] == 42


def test_mv_options_values_response_serializer__with_feature_state__returns_control_value(
    multivariate_feature: Feature,
    environment: Environment,
) -> None:
    # Given
    feature_state = multivariate_feature.feature_states.filter(
        environment=environment,
        identity__isnull=True,
        feature_segment__isnull=True,
    ).first()
    options = list(multivariate_feature.multivariate_options.all())

    payload = {
        "feature_state": feature_state,
        "options": options,
    }

    # When
    serializer = FeatureMVOptionsValuesResponseSerializer(payload)

    # Then
    assert serializer.data["control_value"] == "control"
    assert len(serializer.data["options"]) == 3


def test_mv_options_values_response_serializer__without_feature_state__returns_null_control(
    multivariate_feature: Feature,
) -> None:
    # Given
    options = list(multivariate_feature.multivariate_options.all())

    payload = {
        "feature_state": None,
        "options": options,
    }

    # When
    serializer = FeatureMVOptionsValuesResponseSerializer(payload)

    # Then
    assert serializer.data["control_value"] is None
    assert len(serializer.data["options"]) == 3
