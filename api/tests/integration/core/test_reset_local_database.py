from unittest.mock import MagicMock

import pytest
from django.core.management import CommandError, call_command
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from environments.identities.models import Identity
from environments.models import Environment
from environments.permissions.models import UserEnvironmentPermission
from features.models import Feature, FeatureSegment, FeatureState
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

    # Then: user is created with expected attributes
    user = FFAdminUser.objects.get()
    assert user.email == "local@flagsmith.com"
    assert user.first_name == "Local"
    assert user.last_name == "Developer"
    assert user.check_password("testpass1")

    # Then: organisation is created with expected name
    organisation = Organisation.objects.get()
    assert organisation.name == "Acme, Inc."

    # Then: user has admin role in organisation
    user_organisation = UserOrganisation.objects.get()
    assert user_organisation.user == user
    assert user_organisation.organisation == organisation
    assert user_organisation.role == OrganisationRole.ADMIN.name

    # Then: subscription exists for the organisation
    assert Subscription.objects.filter(organisation=organisation).exists()

    # Then: project is created with expected name
    project = Project.objects.get()
    assert project.name == "AI Booster"
    assert project.organisation == organisation

    # Then: user has project admin access
    user_project_permission = UserProjectPermission.objects.get(user=user)
    assert user_project_permission.project == project
    assert user_project_permission.admin is True

    # Then: environments are created correctly
    environments = Environment.objects.all()
    assert environments.count() == 3
    environment_names = set(environments.values_list("name", flat=True))
    assert environment_names == {"Development", "Staging", "Production"}
    for env in environments:
        assert env.project == project

    # Then: user has admin access to all three environments
    assert UserEnvironmentPermission.objects.filter(user=user, admin=True).count() == 3

    dev_environment = Environment.objects.get(name="Development")

    # Then: features are created with correct attributes
    features = Feature.objects.all()
    assert features.count() == 6

    dark_mode = Feature.objects.get(name="dark_mode")
    assert dark_mode.description == "Enable dark mode theme for the application"
    assert dark_mode.default_enabled is True
    assert dark_mode.type == "FLAG"

    ai_assistant = Feature.objects.get(name="ai_assistant")
    assert ai_assistant.description == "Enable AI-powered assistant features"
    assert ai_assistant.default_enabled is False
    assert ai_assistant.type == "FLAG"

    api_rate_limit = Feature.objects.get(name="api_rate_limit")
    assert api_rate_limit.description == "Maximum API requests per minute"
    assert api_rate_limit.default_enabled is True
    assert api_rate_limit.type == "CONFIG"
    assert api_rate_limit.initial_value == "100"

    welcome_message = Feature.objects.get(name="welcome_message")
    assert welcome_message.description == "Welcome message displayed to users"
    assert welcome_message.default_enabled is True
    assert welcome_message.type == "CONFIG"
    assert welcome_message.initial_value == "Welcome to AI Booster!"

    feature_config = Feature.objects.get(name="feature_config")
    assert feature_config.description == "JSON configuration for feature behavior"
    assert feature_config.default_enabled is True
    assert feature_config.type == "CONFIG"
    assert feature_config.initial_value == '{"theme": "modern", "animations": true}'

    beta_features = Feature.objects.get(name="beta_features")
    assert beta_features.description == "Enable access to beta features"
    assert beta_features.default_enabled is True
    assert beta_features.type == "FLAG"

    # Then: segments are created with correct attributes
    segments = Segment.objects.all()
    assert segments.count() == 3

    premium_segment = Segment.objects.get(name="Premium Users")
    assert (
        premium_segment.description
        == "Users with premium subscription and active status"
    )

    beta_segment = Segment.objects.get(name="Beta Testers")
    assert beta_segment.description == "Users enrolled in beta testing program"

    rollout_segment = Segment.objects.get(name="50% Rollout")
    assert rollout_segment.description == "50% of users for gradual feature rollout"

    # Then: segment overrides are created with correct values
    feature_segments = FeatureSegment.objects.all()
    assert feature_segments.count() == 4
    for feature_segment in feature_segments:
        assert feature_segment.environment == dev_environment

    # dark_mode -> Premium Users
    dark_mode_fs = FeatureSegment.objects.get(
        feature=dark_mode, segment=premium_segment
    )
    dark_mode_override = FeatureState.objects.get(feature_segment=dark_mode_fs)
    assert dark_mode_override.enabled is True

    # beta_features -> Beta Testers
    beta_fs = FeatureSegment.objects.get(feature=beta_features, segment=beta_segment)
    beta_override = FeatureState.objects.get(feature_segment=beta_fs)
    assert beta_override.enabled is True

    # api_rate_limit -> Premium Users with value "500"
    rate_limit_fs = FeatureSegment.objects.get(
        feature=api_rate_limit, segment=premium_segment
    )
    rate_limit_override = FeatureState.objects.get(feature_segment=rate_limit_fs)
    assert rate_limit_override.enabled is True
    assert rate_limit_override.get_feature_state_value() == 500

    # welcome_message -> Beta Testers with value "Welcome, Beta Tester!"
    welcome_fs = FeatureSegment.objects.get(
        feature=welcome_message, segment=beta_segment
    )
    welcome_override = FeatureState.objects.get(feature_segment=welcome_fs)
    assert welcome_override.enabled is True
    assert welcome_override.get_feature_state_value() == "Welcome, Beta Tester!"

    # Then: identities are created
    identities = Identity.objects.all()
    assert identities.count() == 2
    alice = Identity.objects.get(identifier="alice@example.com")
    bob = Identity.objects.get(identifier="bob@example.com")
    assert alice.environment == dev_environment
    assert bob.environment == dev_environment

    # Then: identity overrides are created with correct values
    # alice: dark_mode disabled
    alice_dark_mode = FeatureState.objects.get(identity=alice, feature=dark_mode)
    assert alice_dark_mode.enabled is False

    # bob: welcome_message with custom value
    bob_welcome = FeatureState.objects.get(identity=bob, feature=welcome_message)
    assert bob_welcome.enabled is True
    assert bob_welcome.get_feature_state_value() == "Hello, Bob!"


def test_reset_local_database__raises_error_when_disabled(
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.ENABLE_LOCAL_DATABASE_RESET = False

    # When / Then
    with pytest.raises(CommandError) as exc_info:
        call_command("reset_local_database")

    assert "ENABLE_LOCAL_DATABASE_RESET" in str(exc_info.value)
