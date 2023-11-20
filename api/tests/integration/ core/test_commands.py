import pytest
from django.core.management import call_command
from django.db.models import Model
from djoser.utils import decode_uid
from pytest_django.fixtures import SettingsWrapper
from pytest_lazyfixture import lazy_fixture

from organisations.models import (
    Organisation,
    OrganisationRole,
    UserOrganisation,
)
from projects.models import Project
from users.models import FFAdminUser

pytestmark = pytest.mark.django_db


def _assert_bootstrapped(
    expected_user_email: str,
    expected_organisation_name: str,
    expected_project_name: str,
    capsys: pytest.CaptureFixture,
) -> None:
    # Entity counts are in accordance with the bootstrapped state.
    assert FFAdminUser.objects.count() == 1
    assert Organisation.objects.count() == 1
    assert Project.objects.count() == 1

    # Superuser created as expected.
    user = FFAdminUser.objects.first()
    assert user.email == expected_user_email
    assert user.is_superuser

    # Organisation created as expected.
    organisation = Organisation.objects.first()
    assert organisation.name == expected_organisation_name
    user_organisation = UserOrganisation.objects.first()
    assert user_organisation.user == user
    assert user_organisation.organisation == organisation
    assert user_organisation.role == OrganisationRole.ADMIN

    # Project created as expected.
    project = Project.objects.first()
    assert project.name == expected_project_name
    assert project.organisation == organisation

    # Bootstrap logged as expected.
    capture_result = capsys.readouterr()
    assert not capture_result.err
    assert (
        f'Superuser "{expected_user_email}" created successfully.' in capture_result.out
    )
    assert (
        f'Organisation "{expected_organisation_name}" created successfully.'
        in capture_result.out
    )
    assert (
        f'Project "{expected_project_name}" created successfully.' in capture_result.out
    )

    # The password reset link is correct.
    _, password_reset_url = capture_result.out.split("\n")[1].split(
        "Please go to the following page and choose a password: "
    )
    uid, _ = password_reset_url.split("/confirm/")[1].split("/")

    assert decode_uid(uid) == str(user.pk)


def test_bootstrap__empty_instance__creates_expected(
    settings: SettingsWrapper,
    capsys: pytest.CaptureFixture,
) -> None:
    # Given
    settings.ALLOW_ADMIN_INITIATION_VIA_CLI = True

    expected_user_email = "test@example.com"
    expected_user_password = "foobar"
    expected_organisation_name = "Test Org"
    expected_project_name = "Test Project"

    settings.ADMIN_EMAIL = expected_user_email
    settings.ADMIN_INITIAL_PASSWORD = expected_user_password
    settings.ORGANISATION_NAME = expected_organisation_name
    settings.PROJECT_NAME = expected_project_name

    # When
    call_command("bootstrap")

    # Then
    _assert_bootstrapped(
        expected_user_email=expected_user_email,
        expected_organisation_name=expected_organisation_name,
        expected_project_name=expected_project_name,
        capsys=capsys,
    )


def test_bootstrap__empty_instance__cli_overrides__creates_expected(
    settings: SettingsWrapper,
    capsys: pytest.CaptureFixture,
) -> None:
    # Given
    settings.ALLOW_ADMIN_INITIATION_VIA_CLI = True

    expected_user_email = "test@example.com"
    expected_organisation_name = "Test Org"
    expected_project_name = "Test Project"

    # When
    call_command(
        "bootstrap",
        "--email",
        expected_user_email,
        "--organisation-name",
        expected_organisation_name,
        "--project-name",
        expected_project_name,
    )

    # Then
    _assert_bootstrapped(
        expected_user_email=expected_user_email,
        expected_organisation_name=expected_organisation_name,
        expected_project_name=expected_project_name,
        capsys=capsys,
    )


@pytest.mark.parametrize(
    "existing_data",
    [
        lazy_fixture("admin_user"),
        lazy_fixture("organisation"),
        lazy_fixture("project"),
    ],
)
def test_bootstrap__used_instance__skip_expected(
    settings: SettingsWrapper,
    existing_data: Model,
) -> None:
    # Given
    settings.ALLOW_ADMIN_INITIATION_VIA_CLI = True

    expected_users = [*FFAdminUser.objects.all()]
    expected_organisations = [*Organisation.objects.all()]
    expected_projects = [*Project.objects.all()]

    # When
    call_command("bootstrap")

    # Then
    [*FFAdminUser.objects.all()] == expected_users
    [*Organisation.objects.all()] == expected_organisations
    [*Project.objects.all()] == expected_projects


def test_bootstrap__allow_admin_initiation_via_cli__false_by_default__skip_expected(
    settings: SettingsWrapper,
) -> None:
    # When
    call_command("bootstrap")

    # Then
    assert not FFAdminUser.objects.exists()
    assert not Organisation.objects.exists()
    assert not Project.objects.exists()
