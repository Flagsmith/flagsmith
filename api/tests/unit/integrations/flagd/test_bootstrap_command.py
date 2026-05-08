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
