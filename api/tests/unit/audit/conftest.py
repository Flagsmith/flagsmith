import pytest

from environments.models import Environment
from projects.models import Project


@pytest.fixture()
def mock_dynamo_env_table(mocker):
    return mocker.patch("audit.signals.dynamo_env_table")


@pytest.fixture()
def dynamo_enabled_project(organisation_one):
    return Project.objects.create(
        name="Dynamo enabled project",
        organisation=organisation_one,
        enable_dynamo_db=True,
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
