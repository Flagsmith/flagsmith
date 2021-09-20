import pytest

from features.feature_types import MULTIVARIATE
from features.models import Feature
from features.multivariate.models import MultivariateFeatureOption
from features.value_types import STRING


@pytest.fixture()
def multivariate_feature(project):
    feature = Feature.objects.create(
        name="feature", project=project, type=MULTIVARIATE, initial_value="control"
    )

    multivariate_options = []
    for percentage_allocation in (30, 30, 40):
        string_value = f"multivariate option for {percentage_allocation}% of users."
        multivariate_options.append(
            MultivariateFeatureOption(
                feature=feature,
                default_percentage_allocation=percentage_allocation,
                type=STRING,
                string_value=string_value,
            )
        )

    MultivariateFeatureOption.objects.bulk_create(multivariate_options)
    return feature
