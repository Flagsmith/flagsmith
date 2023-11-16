import io
import sys

import pytest
from django.core.management import call_command
from django.db.models import Model
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
    expected_user_password: str,
    expected_organisation_name: str,
    expected_project_name: str,
) -> None:
    assert FFAdminUser.objects.count() == 1
    assert Organisation.objects.count() == 1
    assert Project.objects.count() == 1

    user = FFAdminUser.objects.first()
    assert user.email == expected_user_email
    assert user.is_superuser
    assert user.check_password(expected_user_password)
    organisation = Organisation.objects.first()
    assert organisation.name == expected_organisation_name
    user_organisation = UserOrganisation.objects.first()
    assert user_organisation.user == user
    assert user_organisation.organisation == organisation
    assert user_organisation.role == OrganisationRole.ADMIN
    project = Project.objects.first()
    assert project.name == expected_project_name
    assert project.organisation == organisation


def test_bootstrap__empty_instance__creates_expected(settings: SettingsWrapper) -> None:
    # Given
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
        expected_user_password=expected_user_password,
        expected_organisation_name=expected_organisation_name,
        expected_project_name=expected_project_name,
    )


def test_bootstrap__empty_instance__cli_overrides__creates_expected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    expected_user_email = "test@example.com"
    expected_user_password = "foobar"
    expected_organisation_name = "Test Org"
    expected_project_name = "Test Project"

    # simulate pipe
    monkeypatch.setattr(sys, "stdin", io.StringIO(expected_user_password + "\n"))

    # When
    call_command(
        "bootstrap",
        "--password-stdin",
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
        expected_user_password=expected_user_password,
        expected_organisation_name=expected_organisation_name,
        expected_project_name=expected_project_name,
    )


@pytest.mark.parametrize(
    "existing_data",
    [
        lazy_fixture("admin_user"),
        lazy_fixture("organisation"),
        lazy_fixture("project"),
    ],
)
def test_bootstrap__used_instance__skip_expected(existing_data: Model) -> None:
    # Given
    expected_users = FFAdminUser.objects.all()
    expected_organisations = Organisation.objects.all()
    expected_projects = Project.objects.all()

    # When
    call_command("bootstrap")

    # Then
    FFAdminUser.objects.all() == expected_users
    Organisation.objects.all() == expected_organisations
    Project.objects.all() == expected_projects
