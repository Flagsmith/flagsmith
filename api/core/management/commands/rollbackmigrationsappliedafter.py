from argparse import ArgumentParser
from datetime import datetime

from django.core.management import BaseCommand, CommandError, call_command
from django.db.migrations.recorder import MigrationRecorder


class Command(BaseCommand):
    """
    Rollback all migrations applied on or after a given datetime.

    Usage: python manage.py rollbackmigrationsappliedafter "2024-10-24 08:23:45"
    """

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "dt",
            type=str,
            help="Rollback all migrations applied on or after this datetime (provided in ISO format)",
        )

    def handle(self, *args, dt: str, **kwargs) -> None:
        try:
            _dt = datetime.fromisoformat(dt)
        except ValueError:
            raise CommandError("Date must be in ISO format")

        applied_migrations = MigrationRecorder.Migration.objects.filter(applied__gte=_dt).order_by("applied")
        if not applied_migrations.exists():
            self.stdout.write(self.style.NOTICE("No migrations to rollback."))

        # Since we've ordered by the date applied, we know that the first entry in the qs for each app
        # is the earliest migration after the supplied date, i.e. we want to roll back to one migration
        # earlier than this one.
        earliest_migration_by_app = {}
        for migration in applied_migrations:
            if migration.app in earliest_migration_by_app:
                continue
            earliest_migration_by_app[migration.app] = migration.name

        for app, migration_name in earliest_migration_by_app.items():
            migration_number = int(migration_name.split("_", maxsplit=1)[0])
            rollback_to = f"{migration_number - 1:04}" if migration_number > 1 else "zero"
            call_command("migrate", app, rollback_to)
