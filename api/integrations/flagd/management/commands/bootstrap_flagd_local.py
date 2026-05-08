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
from organisations.models import Organisation
from projects.models import Project


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

        api_key = (
            EnvironmentAPIKey.objects.filter(
                environment=environment, name=options["api_key_name"]
            )
            .order_by("created_at")
            .first()
        )
        if api_key is None:
            api_key = EnvironmentAPIKey.objects.create(
                environment=environment, name=options["api_key_name"]
            )

        line = f"FLAGSMITH_SERVER_KEY={api_key.key}"
        self.stdout.write(line)

        output: Path | None = options.get("output")
        if output is not None:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(line + "\n")
            self.stdout.write(
                self.style.SUCCESS(f"Wrote {output}")
            )
