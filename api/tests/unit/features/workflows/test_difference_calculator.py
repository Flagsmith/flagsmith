from core.constants import STRING

from features.models import FeatureState
from features.workflows import difference_calculator


def test_get_diff_no_difference(environment, feature):
    # Given
    v1 = FeatureState.objects.get(feature=feature, environment=environment)
    v2 = v1.create_new_version()

    # When
    diff = difference_calculator.get_diff(v1, v2)

    # Then
    assert diff.enabled is None
    assert diff.feature_state_value is None
    assert diff.multivariate_feature_state_values == {}


def test_get_diff_enabled(environment, feature):
    # Given
    v1 = FeatureState.objects.get(feature=feature, environment=environment)
    v2 = v1.create_new_version()
    v2.enabled = not v1.enabled
    v2.save()

    # When
    diff = difference_calculator.get_diff(v1, v2)

    # Then
    assert diff.enabled.from_ == v1.enabled
    assert diff.enabled.to == v2.enabled

    assert diff.feature_state_value is None
    assert diff.multivariate_feature_state_values == {}


def test_get_diff_feature_state_value(environment, feature):
    # Given
    v1 = FeatureState.objects.get(feature=feature, environment=environment)
    v2 = v1.create_new_version()
    v2.feature_state_value.type = STRING
    v2.feature_state_value.string_value = "foo"
    v2.feature_state_value.save()

    # When
    diff = difference_calculator.get_diff(v1, v2)

    # Then
    assert diff.feature_state_value.from_ is None
    assert diff.feature_state_value.to == "foo"

    assert diff.enabled is None
    assert diff.multivariate_feature_state_values == {}


def test_get_diff_mv_feature_state_values(environment, multivariate_feature):
    # Given
    v1 = FeatureState.objects.get(feature=multivariate_feature, environment=environment)
    v2 = v1.create_new_version()

    mv_feature_state_values = v2.multivariate_feature_state_values.order_by("id")
    first = mv_feature_state_values.first()
    last = mv_feature_state_values.last()

    first.percentage_allocation -= 10
    first.save()

    last.percentage_allocation += 10
    last.save()

    # When
    diff = difference_calculator.get_diff(v1, v2)

    # Then
    assert diff.multivariate_feature_state_values != {}

    assert diff.feature_state_value is None
    assert diff.enabled is None
