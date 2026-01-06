from unittest.mock import MagicMock

import pytest
from django.core.management import CommandError, call_command
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from environments.identities.models import Identity
from environments.models import Environment
from environments.permissions.models import UserEnvironmentPermission
from features.models import Feature, FeatureSegment
from organisations.models import (
    Organisation,
    OrganisationRole,
    Subscription,
    UserOrganisation,
)
from projects.models import Project, UserProjectPermission
from segments.models import Segment
from users.models import FFAdminUser

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def enable_local_database_reset(settings: SettingsWrapper) -> None:
    """Enable the reset_local_database command for tests."""
    settings.ENABLE_LOCAL_DATABASE_RESET = True


@pytest.fixture(autouse=True)
def mock_reset_commands(mocker: MockerFixture) -> MagicMock:
    """Mock flush/migrate/createcachetable to avoid resetting the test database."""
    return mocker.patch(
        "core.management.commands.reset_local_database.call_command",
    )


def test_reset_local_database__calls_reset_commands(
    mock_reset_commands: MagicMock,
    mocker: MockerFixture,
) -> None:
    # When
    call_command("reset_local_database")

    # Then
    assert mock_reset_commands.call_args_list == [
        mocker.call("flush", "--noinput", verbosity=0),
        mocker.call("migrate", verbosity=0),
        mocker.call("createcachetable", verbosity=0),
    ]


# Multiple assertions are grouped in this test to avoid running the slow
# reset_local_database command multiple times.
def test_reset_local_database__creates_expected_data() -> None:
    # When
    call_command("reset_local_database")

    # Then: expected entity counts
    assert FFAdminUser.objects.count() == 1
    assert Organisation.objects.count() == 1
    assert Project.objects.count() == 1
    assert Environment.objects.count() == 3
    assert Feature.objects.count() == 6
    assert Segment.objects.count() == 3
    assert FeatureSegment.objects.count() == 4

    # Then: environments are created correctly
    environment_names = set(Environment.objects.values_list("name", flat=True))
    assert environment_names == {"Development", "Staging", "Production"}
    environment = Environment.objects.get(name="Development")
    assert environment.project.name == "AI Booster"

    # Then: feature segments belong to the Development environment
    feature_segments = FeatureSegment.objects.all()
    for feature_segment in feature_segments:
        assert feature_segment.environment == environment

    # Then: user organisation has admin role
    user_organisation = UserOrganisation.objects.first()
    assert user_organisation is not None
    assert user_organisation.role == OrganisationRole.ADMIN.name

    # Then: subscription exists for the organisation
    organisation = Organisation.objects.first()
    assert organisation is not None
    assert Subscription.objects.filter(organisation=organisation).exists()

    # Then: user has project admin access
    user = FFAdminUser.objects.first()
    project = Project.objects.first()
    assert user is not None
    assert project is not None
    user_project_permission = UserProjectPermission.objects.filter(
        user=user, project=project
    ).first()
    assert user_project_permission is not None
    assert user_project_permission.admin is True

    # Then: user has admin access to all three environments
    assert UserEnvironmentPermission.objects.filter(user=user, admin=True).count() == 3

    # Then: identities are created
    assert Identity.objects.count() == 2
    identifiers = list(Identity.objects.values_list("identifier", flat=True))
    assert "alice@example.com" in identifiers
    assert "bob@example.com" in identifiers


def test_reset_local_database__raises_error_when_disabled(
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.ENABLE_LOCAL_DATABASE_RESET = False

    # When / Then
    with pytest.raises(CommandError) as exc_info:
        call_command("reset_local_database")

    assert "ENABLE_LOCAL_DATABASE_RESET" in str(exc_info.value)
