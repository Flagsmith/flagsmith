from django.core.management.base import BaseCommand, CommandError

from environments.dynamodb import DynamoIdentityWrapper


class Command(BaseCommand):
    help = "Migrate Identity Data to Dynamo db"

    def add_arguments(self, parser):
        parser.add_argument(
            "project", type=int, help="Id of the project being migrated"
        )
        parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="Force migrate Identities of the project",
        )

    def handle(self, *args, **options):
        project_id = options["project"]
        identity_wrapper = DynamoIdentityWrapper()
        if identity_wrapper.is_migration_done(project_id) and not options["force"]:
            raise CommandError(
                "Identities for this project are already migrated. Use -f to force migrate"
            )
        identity_wrapper.migrate_identities(project_id)
