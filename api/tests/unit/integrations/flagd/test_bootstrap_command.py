"""
Tests for the ``bootstrap_flagd_local`` management command, which is
the local-dev shortcut for minting a server-side environment key
without touching the UI.
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command

from environments.models import Environment, EnvironmentAPIKey
from organisations.models import Organisation
from projects.models import Project
from users.models import FFAdminUser


@pytest.mark.django_db
def test_bootstrap_flagd_local__fresh_database__creates_org_project_env_and_key() -> None:
    # Given an empty database
    # When the command runs with defaults
    out = StringIO()
    call_command("bootstrap_flagd_local", stdout=out)

    # Then it prints a server-side key
    output = out.getvalue().strip().splitlines()[0]
    assert output.startswith("FLAGSMITH_SERVER_KEY=ser.")

    # And persists the entire org/project/env/key chain
    organisation = Organisation.objects.get(name="local-dev")
    project = Project.objects.get(name="local-dev", organisation=organisation)
    environment = Environment.objects.get(name="development", project=project)
    api_key = EnvironmentAPIKey.objects.get(
        environment=environment, name="flagd-local"
    )
    assert output.endswith(api_key.key)


@pytest.mark.django_db
def test_bootstrap_flagd_local__existing_resources__reuses_them() -> None:
    # Given an existing org/project/env/key
    organisation = Organisation.objects.create(name="local-dev")
    project = Project.objects.create(name="local-dev", organisation=organisation)
    environment = Environment.objects.create(name="development", project=project)
    existing_key = EnvironmentAPIKey.objects.create(
        environment=environment, name="flagd-local"
    )

    # When the command runs again
    out = StringIO()
    call_command("bootstrap_flagd_local", stdout=out)

    # Then it does NOT create duplicates
    assert Organisation.objects.filter(name="local-dev").count() == 1
    assert Project.objects.filter(name="local-dev").count() == 1
    assert Environment.objects.filter(name="development", project=project).count() == 1
    assert (
        EnvironmentAPIKey.objects.filter(
            environment=environment, name="flagd-local"
        ).count()
        == 1
    )
    # And it returns the same key
    assert out.getvalue().strip().splitlines()[0].endswith(existing_key.key)


@pytest.mark.django_db
def test_bootstrap_flagd_local__output_path__writes_env_file(
    tmp_path: Path,
) -> None:
    # Given a target output file
    output = tmp_path / "subdir" / "flagd.env"

    # When the command runs with --output
    call_command(
        "bootstrap_flagd_local", "--output", str(output), stdout=StringIO()
    )

    # Then the env file is created with the key
    assert output.exists()
    content = output.read_text().strip()
    assert content.startswith("FLAGSMITH_SERVER_KEY=ser.")


@pytest.mark.django_db
def test_bootstrap_flagd_local__fresh_database__creates_logged_in_admin() -> None:
    # Given an empty database
    # When the command runs
    call_command("bootstrap_flagd_local", stdout=StringIO())

    # Then the admin user is created with a working password and attached
    # to the bootstrapped organisation
    admin = FFAdminUser.objects.get(email="admin@example.com")
    assert admin.check_password("admin")
    assert admin.is_active and admin.is_superuser and admin.is_staff
    organisation = Organisation.objects.get(name="local-dev")
    assert admin.belongs_to(organisation.id)


@pytest.mark.django_db
def test_bootstrap_flagd_local__existing_admin_with_old_password__refreshes_password() -> None:
    # Given an existing admin with a stale password
    admin = FFAdminUser.objects.create_superuser(  # type: ignore[no-untyped-call]
        email="admin@example.com", is_active=True, password="old-password"
    )

    # When the command runs with a new password
    call_command(
        "bootstrap_flagd_local", "--admin-password", "new-password",
        stdout=StringIO(),
    )

    # Then the new password works
    admin.refresh_from_db()
    assert admin.check_password("new-password")


@pytest.mark.django_db
def test_bootstrap_flagd_local__api_key_option__pins_environment_key_to_value() -> None:
    # Given a desired well-known local-dev key
    chosen = "ser.local-dev-pinned"

    # When the command runs with --api-key
    out = StringIO()
    call_command("bootstrap_flagd_local", "--api-key", chosen, stdout=out)

    # Then the EnvironmentAPIKey carries that value
    environment = Environment.objects.get(name="development")
    api_key = EnvironmentAPIKey.objects.get(
        environment=environment, name="flagd-local"
    )
    assert api_key.key == chosen
    assert out.getvalue().strip().splitlines()[0] == f"FLAGSMITH_SERVER_KEY={chosen}"


@pytest.mark.django_db
def test_bootstrap_flagd_local__api_key_option__rotates_existing_value() -> None:
    # Given an existing env + auto-generated key
    call_command("bootstrap_flagd_local", stdout=StringIO())
    environment = Environment.objects.get(name="development")
    original_key = EnvironmentAPIKey.objects.get(
        environment=environment, name="flagd-local"
    ).key
    assert original_key.startswith("ser.")

    # When the command runs again with --api-key
    chosen = "ser.local-dev-rotated"
    call_command(
        "bootstrap_flagd_local", "--api-key", chosen, stdout=StringIO()
    )

    # Then the existing record is updated to the chosen value
    api_key = EnvironmentAPIKey.objects.get(
        environment=environment, name="flagd-local"
    )
    assert api_key.key == chosen


@pytest.mark.django_db
def test_bootstrap_flagd_local__api_key_without_ser_prefix__raises() -> None:
    # Given a bogus key without the required prefix
    # When the command runs
    # Then it raises before touching the database
    with pytest.raises(ValueError, match="must start with 'ser.'"):
        call_command(
            "bootstrap_flagd_local", "--api-key", "client-side-key",
            stdout=StringIO(),
        )


@pytest.mark.django_db
def test_bootstrap_flagd_local__custom_names__honours_options() -> None:
    # Given custom org/project/env names
    out = StringIO()

    # When the command runs with overrides
    call_command(
        "bootstrap_flagd_local",
        "--organisation", "my-org",
        "--project", "my-app",
        "--environment", "staging",
        "--api-key-name", "ci-flagd",
        stdout=out,
    )

    # Then the named resources exist and the key carries the chosen label
    organisation = Organisation.objects.get(name="my-org")
    project = Project.objects.get(name="my-app", organisation=organisation)
    environment = Environment.objects.get(name="staging", project=project)
    EnvironmentAPIKey.objects.get(environment=environment, name="ci-flagd")
