from argparse import ArgumentParser
from datetime import datetime

from django.core.management import BaseCommand, CommandError, call_command
from django.db.migrations.recorder import MigrationRecorder


class Command(BaseCommand):
    """
    Rollback all migrations applied on or after a given datetime.

    Usage: python manage.py rollbackmigrationsappliedafter "2024-10-24 08:23:45"
    """

    def add_arguments(self, parser: ArgumentParser):  # type: ignore[no-untyped-def]
        parser.add_argument(
            "dt",
            type=str,
            help="Rollback all migrations applied on or after this datetime (provided in ISO format)",
        )

    def handle(self, *args, dt: str, **kwargs) -> None:  # type: ignore[no-untyped-def]
        try:
            _dt = datetime.fromisoformat(dt)
        except ValueError:
            raise CommandError("Date must be in ISO format")

        applied_migrations = MigrationRecorder.Migration.objects.filter(
            applied__gte=_dt
        ).order_by("applied")
        if not applied_migrations.exists():
            self.stdout.write(self.style.NOTICE("No migrations to rollback."))

        # Since we've ordered by the date applied, we know that the first entry in the qs for each app
        # is the earliest migration after the supplied date.
        earliest_migration_by_app = {}
        for migration in applied_migrations:
            if migration.app in earliest_migration_by_app:
                continue
            earliest_migration_by_app[migration.app] = migration.name

        for app, migration_name in earliest_migration_by_app.items():
            call_command("migrate", app, _get_previous_migration_number(migration_name))


def _get_previous_migration_number(migration_name: str) -> str:
    """
    Returns the previous migration number (0 padded number to 4 characters), or zero
    if the provided migration name is the first for a given app (usually 0001_initial).

    Examples:
          _get_previous_migration_number("0001_initial") -> "zero"
          _get_previous_migration_number("0009_migration_9") -> "0008"
          _get_previous_migration_number("0103_migration_103") -> "0102"
    """

    migration_number = int(migration_name.split("_", maxsplit=1)[0])
    return f"{migration_number - 1:04}" if migration_number > 1 else "zero"
