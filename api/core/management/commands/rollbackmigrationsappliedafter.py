from argparse import ArgumentParser
from datetime import datetime, timezone

from django.core.management import BaseCommand, CommandError, call_command
from django.db.migrations.recorder import MigrationRecorder


class Command(BaseCommand):
    """
    Rollback all migrations applied on or after a given date.

    Usage: python manage.py rollbackmigrationsappliedafter --date 2024-10-24
    """

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--date",
            type=str,
            required=True,
            help="Rollback all migrations applied on or after this UTC date (provided in the format YYYY-MM-DD)",
        )

    def handle(self, *args, date: str, **kwargs) -> None:
        try:
            _date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            raise CommandError("Date must be in format YYYY-MM-DD")

        applied_migrations = MigrationRecorder.Migration.objects.filter(applied__gte=_date)
        for migration in applied_migrations:
            migration_number = migration.name.split("_", maxsplit=1)[0]
            rollback_to = int(migration_number) - 1
            call_command("migrate", migration.app, f"{rollback_to:04}")
