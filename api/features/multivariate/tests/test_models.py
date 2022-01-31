import pytest
from django.core.exceptions import ValidationError

from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)


def test_validate_percentage_allocations_raises_error_for_invalid_percentage_allocation(
    feature,
):
    # Given
    option_1 = MultivariateFeatureOption.objects.create(
        default_percentage_allocation=50, string_value="opt_1", feature=feature
    )
    MultivariateFeatureOption.objects.create(
        default_percentage_allocation=50, string_value="opt_2", feature=feature
    )
    mv_fs = MultivariateFeatureStateValue.objects.get(
        multivariate_feature_option=option_1
    )

    # When
    mv_fs.percentage_allocation = 100

    # Then
    with pytest.raises(ValidationError):
        mv_fs.save()


def test_validate_percentage_allocations_works_for_valid_percentage_allocation(feature):
    # Given
    option_1 = MultivariateFeatureOption.objects.create(
        default_percentage_allocation=50, string_value="opt_1", feature=feature
    )
    MultivariateFeatureOption.objects.create(
        default_percentage_allocation=40, string_value="opt_2", feature=feature
    )
    mv_fs = MultivariateFeatureStateValue.objects.get(
        multivariate_feature_option=option_1
    )

    # When
    mv_fs.percentage_allocation = 50

    # Then
    mv_fs.save()
