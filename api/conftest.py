import pytest
from rest_framework.test import APIClient

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment
from features.models import Feature
from organisations.models import Organisation
from projects.models import Project


@pytest.fixture()
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture()
def organisation(db, admin_user):
    org = Organisation.objects.create(name="Test Org")
    admin_user.add_organisation(org)
    return org


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


@pytest.fixture()
def feature(project, environment):
    return Feature.objects.create(name="Test Feature1", project=project)
