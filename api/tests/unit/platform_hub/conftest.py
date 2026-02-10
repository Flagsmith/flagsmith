import pytest
from django.conf import settings
from rest_framework.test import APIClient

from environments.models import Environment
from features.models import Feature
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from users.models import FFAdminUser


@pytest.fixture
def use_analytics_db(request: pytest.FixtureRequest) -> None:
    if "analytics" not in settings.DATABASES:  # pragma: no cover
        pytest.skip("No analytics database configured, skipping")
        return
    request.applymarker(pytest.mark.django_db(databases=["default", "analytics"]))
    request.getfixturevalue("db")


@pytest.fixture(autouse=True)
def use_analytics_db_marked(request: pytest.FixtureRequest) -> None:
    if request.node.get_closest_marker("use_analytics_db"):
        request.getfixturevalue("use_analytics_db")


@pytest.fixture()
def platform_hub_organisation(db: None) -> Organisation:
    org: Organisation = Organisation.objects.create(name="Platform Hub Org")
    return org


@pytest.fixture()
def other_organisation(db: None) -> Organisation:
    org: Organisation = Organisation.objects.create(name="Other Org")
    return org


@pytest.fixture()
def platform_hub_admin_user(
    platform_hub_organisation: Organisation,
) -> FFAdminUser:
    user: FFAdminUser = FFAdminUser.objects.create_user(  # type: ignore[no-untyped-call]
        email="platform-hub-admin@test.com",
        password="testpass123!",
    )
    user.add_organisation(platform_hub_organisation, role=OrganisationRole.ADMIN)
    return user


@pytest.fixture()
def platform_hub_admin_client(
    platform_hub_admin_user: FFAdminUser,
) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=platform_hub_admin_user)
    return client


@pytest.fixture()
def platform_hub_project(
    platform_hub_organisation: Organisation,
) -> Project:
    project: Project = Project.objects.create(
        name="Hub Project",
        organisation=platform_hub_organisation,
    )
    return project


@pytest.fixture()
def platform_hub_environment(
    platform_hub_project: Project,
) -> Environment:
    env: Environment = Environment.objects.create(
        name="Hub Environment",
        project=platform_hub_project,
    )
    return env


@pytest.fixture()
def platform_hub_feature(
    platform_hub_project: Project,
    platform_hub_environment: Environment,
) -> Feature:
    feature: Feature = Feature.objects.create(
        name="hub_feature",
        project=platform_hub_project,
    )
    return feature


@pytest.fixture()
def other_org_project(other_organisation: Organisation) -> Project:
    project: Project = Project.objects.create(
        name="Other Project",
        organisation=other_organisation,
    )
    return project


@pytest.fixture()
def other_org_environment(other_org_project: Project) -> Environment:
    env: Environment = Environment.objects.create(
        name="Other Environment",
        project=other_org_project,
    )
    return env


@pytest.fixture()
def other_org_feature(
    other_org_project: Project,
    other_org_environment: Environment,
) -> Feature:
    feature: Feature = Feature.objects.create(
        name="other_feature",
        project=other_org_project,
    )
    return feature
