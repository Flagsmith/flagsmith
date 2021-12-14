import pytest

from environments.models import Environment
from features.models import Feature
from organisations.models import Organisation
from projects.models import Project
from users.models import FFAdminUser


@pytest.fixture()
def organisation_one(db):
    return Organisation.objects.create(name="Test organisation 1")


@pytest.fixture()
def organisation_two(db):
    return Organisation.objects.create(name="Test organisation 2")


@pytest.fixture()
def organisation_one_project_one(organisation_one):
    return Project.objects.create(name="Test Project 1", organisation=organisation_one)


@pytest.fixture()
def organisation_one_project_two(organisation_one):
    return Project.objects.create(name="Test Project 2", organisation=organisation_one)


@pytest.fixture()
def organisation_two_project_one(organisation_two):
    return Project.objects.create(name="Test Project 1", organisation=organisation_two)


@pytest.fixture()
def organisation_two_project_two(organisation_two):
    return Project.objects.create(name="Test Project 2", organisation=organisation_two)


@pytest.fixture()
def organisation_one_project_one_environment_one(organisation_one_project_one):
    return Environment.objects.create(
        name="Test Environment 1", project=organisation_one_project_one
    )


@pytest.fixture()
def organisation_one_project_one_environment_two(organisation_one_project_one):
    return Environment.objects.create(
        name="Test Environment 2", project=organisation_one_project_one
    )


@pytest.fixture()
def organisation_two_project_one_environment_one(organisation_two_project_one):
    return Environment.objects.create(
        name="Test Environment 1", project=organisation_two_project_one
    )


@pytest.fixture()
def organisation_two_project_one_environment_two(organisation_two_project_one):
    return Environment.objects.create(
        name="Test Environment 2", project=organisation_two_project_one
    )


@pytest.fixture()
def user_one():
    return FFAdminUser.objects.create(email="test@example.com")


@pytest.fixture()
def organisation_one_user(user_one, organisation_one):
    user_one.add_organisation(organisation_one)
    return user_one


@pytest.fixture()
def organisation_one_project_one_feature_one(organisation_one_project_one):
    return Feature.objects.create(
        project=organisation_one_project_one,
        name="feature_1",
        initial_value="feature_1_value",
    )
