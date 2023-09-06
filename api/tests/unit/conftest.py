import pytest

from environments.models import Environment
from features.models import Feature
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from projects.tags.models import Tag
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
def organisation_one_admin_user(organisation_one):
    organisation_one_admin_user = FFAdminUser.objects.create(
        email="org1_admin@example.com"
    )
    organisation_one_admin_user.add_organisation(
        organisation_one, role=OrganisationRole.ADMIN
    )
    return organisation_one_admin_user


@pytest.fixture()
def organisation_one_project_one_feature_one(organisation_one_project_one):
    return Feature.objects.create(
        project=organisation_one_project_one,
        name="feature_1",
        initial_value="feature_1_value",
    )


@pytest.fixture()
def dynamo_enabled_project(organisation):
    return Project.objects.create(
        name="Dynamo enabled project",
        organisation=organisation,
        enable_dynamo_db=True,
    )


@pytest.fixture()
def realtime_enabled_project(organisation_one):
    return Project.objects.create(
        name="Realtime enabled project",
        organisation=organisation_one,
        enable_realtime_updates=True,
    )


@pytest.fixture()
def realtime_enabled_project_environment_one(realtime_enabled_project):
    return Environment.objects.create(
        name="Env 1 realtime",
        project=realtime_enabled_project,
        api_key="env-1-realtime-key",
    )


@pytest.fixture()
def realtime_enabled_project_environment_two(realtime_enabled_project):
    return Environment.objects.create(
        name="Env 2 realtime",
        project=realtime_enabled_project,
        api_key="env-2-realtime-key",
    )


@pytest.fixture()
def dynamo_enabled_project_environment_one(dynamo_enabled_project):
    return Environment.objects.create(
        name="Env 1", project=dynamo_enabled_project, api_key="env-1-key"
    )


@pytest.fixture()
def dynamo_enabled_project_environment_two(dynamo_enabled_project):
    return Environment.objects.create(
        name="Env 2", project=dynamo_enabled_project, api_key="env-2-key"
    )


@pytest.fixture()
def tag_one(project):
    return Tag.objects.create(
        label="Test Tag",
        color="#fffff",
        description="Test Tag description",
        project=project,
    )


@pytest.fixture()
def tag_two(project):
    return Tag.objects.create(
        label="Test Tag2",
        color="#fffff",
        description="Test Tag2 description",
        project=project,
    )


@pytest.fixture()
def project_two(organisation: Organisation) -> Project:
    return Project.objects.create(name="Test Project Two", organisation=organisation)


@pytest.fixture()
def environment_two(project: Project) -> Environment:
    return Environment.objects.create(name="Test Environment two", project=project)


@pytest.fixture
def project_two_environment(project_two: Project) -> Environment:
    return Environment.objects.create(
        name="Test Project two Environment", project=project_two
    )


@pytest.fixture
def project_two_feature(project_two: Project) -> Feature:
    return Feature.objects.create(
        name="project_two_feature", project=project_two, initial_value="initial_value"
    )
