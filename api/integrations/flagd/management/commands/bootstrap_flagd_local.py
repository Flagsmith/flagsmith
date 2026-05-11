"""
Idempotent bootstrap helper for local flagd development.

Creates (or reuses) an Organisation, Project, Environment, and
server-side ``EnvironmentAPIKey``, then writes the resulting key to
stdout — and optionally to a shell-sourceable env file. Designed to be
run from a docker-compose init service so flagd can pick up the key
without any manual UI clicks.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

from environments.models import Environment, EnvironmentAPIKey
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from users.models import FFAdminUser


class Command(BaseCommand):
    help = "Create or reuse a local Flagsmith env and emit a server-side key for flagd."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--organisation",
            default="local-dev",
            help="Organisation name (default: local-dev).",
        )
        parser.add_argument(
            "--project",
            default="local-dev",
            help="Project name (default: local-dev).",
        )
        parser.add_argument(
            "--environment",
            default="development",
            help="Environment name (default: development).",
        )
        parser.add_argument(
            "--api-key-name",
            default="flagd-local",
            help="EnvironmentAPIKey label (default: flagd-local).",
        )
        parser.add_argument(
            "--api-key",
            default=None,
            help=(
                "Force the EnvironmentAPIKey value to a specific server-side "
                "key (must start with `ser.`). Useful for local-dev where the "
                "key must be known at compose-parse time. Default: auto-generate."
            ),
        )
        parser.add_argument(
            "--admin-email",
            default="admin@example.com",
            help="Email for the local admin user (default: admin@example.com).",
        )
        parser.add_argument(
            "--admin-password",
            default="admin",
            help=(
                "Password to set on the local admin user. Always overwritten "
                "on each run so the local dev experience stays predictable. "
                "Default: admin."
            ),
        )
        parser.add_argument(
            "--output",
            type=Path,
            help=(
                "If given, write `FLAGSMITH_SERVER_KEY=...` to this file. "
                "Useful for sourcing from a docker-compose init service."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        organisation, _ = Organisation.objects.get_or_create(
            name=options["organisation"]
        )
        project, _ = Project.objects.get_or_create(
            name=options["project"], organisation=organisation
        )
        environment, _ = Environment.objects.get_or_create(
            name=options["environment"], project=project
        )

        # Create or refresh the local admin user so the operator can
        # log into the Flagsmith UI without juggling password-reset
        # links. The user is attached to the organisation so they land
        # straight in the bootstrapped project on login.
        admin_email = options["admin_email"]
        admin_password = options["admin_password"]
        admin = FFAdminUser.objects.filter(email=admin_email).first()
        if admin is None:
            admin = FFAdminUser.objects.create_superuser(  # type: ignore[no-untyped-call]
                email=admin_email,
                is_active=True,
                password=admin_password,
            )
        else:
            admin.set_password(admin_password)
            admin.is_active = True
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()
        if not admin.belongs_to(organisation.id):
            admin.add_organisation(organisation, role=OrganisationRole.ADMIN)

        forced_key: str | None = options.get("api_key")
        if forced_key and not forced_key.startswith("ser."):
            raise ValueError(
                "--api-key must start with 'ser.' to be accepted by the flagd "
                f"sync endpoint; got {forced_key!r}."
            )

        api_key = (
            EnvironmentAPIKey.objects.filter(
                environment=environment, name=options["api_key_name"]
            )
            .order_by("created_at")
            .first()
        )
        if api_key is None:
            create_kwargs: dict[str, Any] = {
                "environment": environment,
                "name": options["api_key_name"],
            }
            if forced_key:
                create_kwargs["key"] = forced_key
            api_key = EnvironmentAPIKey.objects.create(**create_kwargs)
        elif forced_key and api_key.key != forced_key:
            api_key.key = forced_key
            api_key.save()

        line = f"FLAGSMITH_SERVER_KEY={api_key.key}"
        self.stdout.write(line)
        self.stdout.write(
            self.style.SUCCESS(
                f"Admin user: {admin_email} / {admin_password}"
            )
        )

        output: Path | None = options.get("output")
        if output is not None:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(line + "\n")
            self.stdout.write(
                self.style.SUCCESS(f"Wrote {output}")
            )
