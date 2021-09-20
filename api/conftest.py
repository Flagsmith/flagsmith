import pytest

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment
from features.feature_types import MULTIVARIATE
from features.models import Feature
from features.multivariate.models import MultivariateFeatureOption
from features.value_types import INTEGER, STRING
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
def trait(identity):
    return Trait.objects.create(identity=identity)
