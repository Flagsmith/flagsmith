import pytest

from environments.identities.models import Identity
from environments.models import Environment
from features.feature_types import MULTIVARIATE
from features.models import Feature
from features.multivariate.models import MultivariateFeatureOption
from features.value_types import STRING, INTEGER
from organisations.models import Organisation
from projects.models import Project


@pytest.fixture()
def organisation(db):
    return Organisation.objects.create(name="Test Org")


@pytest.fixture()
def project(organisation):
    return Project.objects.create(name="Test Project", organisation=organisation)


@pytest.fixture()
def environment(project):
    return Environment.objects.create(name="Test Environment", project=project)


@pytest.fixture()
def identity(environment):
    return Identity.objects.create(identifier="test_identity", environment=environment)


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
