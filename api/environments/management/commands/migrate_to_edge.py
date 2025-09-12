from django.core.management.base import BaseCommand, CommandError

from environments.dynamodb.migrator import IdentityMigrator


class Command(BaseCommand):
    help = "Migrate Identity Data to Dynamo db"

    def add_arguments(self, parser):  # type: ignore[no-untyped-def]
        parser.add_argument(
            "project", type=int, help="Id of the project being migrated"
        )

    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        project_id = options["project"]
        identity_migrator = IdentityMigrator(project_id)  # type: ignore[no-untyped-call]
        if not identity_migrator.can_migrate:
            raise CommandError(
                "Identities migration for this project is either done or is in progress"
            )
        identity_migrator.migrate()  # type: ignore[no-untyped-call]
