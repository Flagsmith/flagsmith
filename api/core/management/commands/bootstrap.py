import argparse
from typing import Any

from django.core.management import BaseCommand

from organisations.management.commands.createinitialorganisation import (
    Command as CreateInitialOrganisationCommand,
)
from projects.management.commands.createinitialproject import (
    Command as CreateInitialProjectCommand,
)
from users.management.commands.createinitialadminuser import (
    Command as CreateInitialAdminUserCommand,
)


class Command(BaseCommand):
    def create_parser(self, *args: Any, **kwargs: Any) -> argparse.ArgumentParser:
        return super().create_parser(*args, conflict_handler="resolve", **kwargs)

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        CreateInitialAdminUserCommand.add_arguments(self, parser)
        CreateInitialOrganisationCommand.add_arguments(self, parser)
        CreateInitialProjectCommand.add_arguments(self, parser)

    def handle(self, *args: Any, **kwargs: Any) -> None:
        CreateInitialAdminUserCommand.handle(self, *args, **kwargs)
        CreateInitialOrganisationCommand.handle(self, *args, **kwargs)
        CreateInitialProjectCommand.handle(self, *args, **kwargs)
